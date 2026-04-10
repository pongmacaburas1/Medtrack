"""
Management command: simulate_workflow

Simulates the complete 7-day clinical workflow for PDL profiles:
  Step 1 — Initial consultation   (COMPLETED, with physical exam + PMH data)
  Step 2 — 7-day medication prescription (DISPENSED, inventory deducted)
  Step 3 — Follow-up consultation (COMPLETED if date is past, SCHEDULED if future)
           Records findings: whether patient responded to medication or needs ongoing care.

Prerequisites: run `python manage.py initialize` first (creates physicians, locations,
               medications, and inventory).  Then run `python manage.py generate_pdl_data`
               to have 150 sample PDL profiles.

Usage:
    python manage.py simulate_workflow
    python manage.py simulate_workflow --count 80
    python manage.py simulate_workflow --clear
"""

import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from consultations.models import (
    Consultation,
    ConsultationLocation,
    ConsultationReason,
    ConsultationTimeBlock,
    Physician,
)
from medications.models import (
    Medication,
    MedicationInventory,
    MedicationPrescription,
    Pharmacist,
)
from pdl.models import HealthCondition, PDLProfile


# ---------------------------------------------------------------------------
# Condition → medication mapping
# (med_name, dosage, frequency, duration_label, qty_per_7_days)
# ---------------------------------------------------------------------------
CONDITION_MED_MAP = {
    'HTN':    ('Amlodipine',   '5mg',   'once a day',       '7 days', 7),
    'DM':     ('Simvastatin',  '20mg',  'once a day',       '7 days', 7),
    'HEART':  ('Clopidogrel',  '75mg',  'once a day',       '7 days', 7),
    'ASTHMA': ('Montelukast',  '10mg',  'once a day',       '7 days', 7),
    'TB':     ('Amoxil',       '500mg', '3 times a day',    '7 days', 21),
    'MENTAL': ('Sertraline',   '50mg',  'once a day',       '7 days', 7),
    'RENAL':  ('Omeprazole',   '20mg',  'once a day',       '7 days', 7),
    'CANCER': ('Advil',        '200mg', '3 times a day',    '7 days', 21),
    'OTHER':  ('Cetirizine',   '10mg',  'once a day',       '7 days', 7),
}
FALLBACK_MED = ('Tylenol', '500mg', 'every 6 hours as needed', '7 days', 14)

# Condition labels for notes
CONDITION_LABELS = dict(HealthCondition.CONDITION_CHOICES)

# Time block names ordered for iteration
ALL_TIME_BLOCKS = [b.name for b in ConsultationTimeBlock]


# ---------------------------------------------------------------------------
# Vital-sign generators
# ---------------------------------------------------------------------------

def _gen_initial_vitals(condition_codes: set) -> dict:
    """Realistic admission-day vital signs based on health conditions."""
    height = round(random.uniform(155.0, 178.0), 1)
    weight = round(random.uniform(52.0, 88.0), 1)
    bmi    = round(weight / ((height / 100) ** 2), 1)
    temp   = round(random.uniform(36.4, 37.2), 1)
    hr     = random.randint(62, 88)
    rr     = random.randint(14, 18)

    # Hypertension / Heart disease → elevated BP
    if 'HTN' in condition_codes or 'HEART' in condition_codes:
        sbp = random.randint(145, 168)
        dbp = random.randint(90, 102)
        hr  = random.randint(75, 96)
    else:
        sbp = random.randint(108, 128)
        dbp = random.randint(68, 84)

    # TB / Cancer → fever and lower weight
    if 'TB' in condition_codes or 'CANCER' in condition_codes:
        temp   = round(random.uniform(37.8, 39.2), 1)
        weight = round(random.uniform(42.0, 62.0), 1)
        bmi    = round(weight / ((height / 100) ** 2), 1)
        rr     = random.randint(18, 24)

    # Asthma → higher respiratory rate
    if 'ASTHMA' in condition_codes:
        rr = random.randint(20, 26)
        hr = random.randint(80, 102)

    return {
        'pea_temperature':   temp,
        'pea_blood_pressure': f"{sbp}/{dbp}",
        'pea_heart_rate':    hr,
        'pea_rr':            rr,
        'pea_height':        height,
        'pea_weight':        weight,
        'pea_bmi':           bmi,
    }


def _gen_followup_vitals(condition_codes: set, initial_vitals: dict) -> dict:
    """
    Follow-up vitals after 7 days of medication — generally improved,
    but chronic conditions show only moderate improvement.
    """
    height = initial_vitals['pea_height']
    weight = initial_vitals['pea_weight']
    bmi    = initial_vitals['pea_bmi']
    temp   = round(random.uniform(36.4, 36.9), 1)   # resolved fever
    hr     = random.randint(62, 84)
    rr     = random.randint(14, 18)

    # HTN / Heart: some improvement, still may be elevated
    if 'HTN' in condition_codes or 'HEART' in condition_codes:
        sbp = random.randint(130, 150)
        dbp = random.randint(82, 94)
        hr  = random.randint(68, 88)
    else:
        sbp = random.randint(108, 125)
        dbp = random.randint(68, 82)

    # Recovering TB / Cancer: slight weight gain, normal temp
    if 'TB' in condition_codes or 'CANCER' in condition_codes:
        weight = round(weight + random.uniform(0.2, 1.5), 1)
        bmi    = round(weight / ((height / 100) ** 2), 1)

    # Asthma: improved RR
    if 'ASTHMA' in condition_codes:
        rr = random.randint(16, 20)

    return {
        'pea_temperature':    temp,
        'pea_blood_pressure': f"{sbp}/{dbp}",
        'pea_heart_rate':     hr,
        'pea_rr':             rr,
        'pea_height':         height,
        'pea_weight':         weight,
        'pea_bmi':            bmi,
    }


# ---------------------------------------------------------------------------
# Slot allocator — prevents unique-constraint violations
# ---------------------------------------------------------------------------

class SlotAllocator:
    """
    Tracks used (date, block) combinations per physician/location/PDL,
    pre-loading from the existing Consultation table.
    """

    def __init__(self, physician: Physician):
        self.physician = physician
        self._physician_slots: set[tuple] = set()
        self._location_slots:  set[tuple] = set()
        self._pdl_slots:       set[tuple] = set()

        for c in Consultation.objects.filter(physician=physician):
            d, b = c.consultation_date_date_only, c.consultation_time_block
            self._physician_slots.add((d, b))
            if c.location_id:
                self._location_slots.add((c.location_id, d, b))
            self._pdl_slots.add((c.pdl_profile_id, d, b))

    def allocate(
        self,
        pdl: PDLProfile,
        locations: list,
        preferred_date: date,
        max_days: int = 90,
    ) -> tuple:
        """
        Find the first free (date, block, location) starting from preferred_date.
        Returns (date, block, location) or (None, None, None) if none found.
        """
        for day_offset in range(max_days):
            day = preferred_date + timedelta(days=day_offset)
            for block in ALL_TIME_BLOCKS:
                if (day, block) in self._physician_slots:
                    continue
                if (pdl.id, day, block) in self._pdl_slots:
                    continue
                for loc in locations:
                    if (loc.id, day, block) not in self._location_slots:
                        # Reserve the slot
                        self._physician_slots.add((day, block))
                        self._location_slots.add((loc.id, day, block))
                        self._pdl_slots.add((pdl.id, day, block))
                        return day, block, loc
        return None, None, None


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Simulate the full 7-day clinical workflow: "
        "initial consultation → 7-day prescription → follow-up consultation."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=80,
            help='Number of PDL profiles to simulate (default: 80)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all SIMULATED consultations and prescriptions before running.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count    = options['count']
        do_clear = options['clear']
        today    = date.today()

        # ── 1. Load prerequisite objects ─────────────────────────────────────
        physician = Physician.objects.select_related('username').first()
        if not physician:
            self.stdout.write(self.style.ERROR(
                'No physician found. Run: python manage.py initialize'
            ))
            return

        locations = list(ConsultationLocation.objects.all())
        if not locations:
            self.stdout.write(self.style.ERROR(
                'No consultation locations found. Run: python manage.py initialize'
            ))
            return

        pharmacist = Pharmacist.objects.first()
        if not pharmacist:
            self.stdout.write(self.style.ERROR(
                'No pharmacist found. Run: python manage.py initialize'
            ))
            return

        reason_initial  = self._get_or_create_reason('Routine Checkup',  'General health checkup.')
        reason_followup = self._get_or_create_reason('Follow-up Visit',  'Follow-up on previous condition.')
        reason_medreview = self._get_or_create_reason('Medication Review', 'Review of current medications and treatment progress.')

        # ── 2. Optionally clear previous simulated data ──────────────────────
        if do_clear:
            deleted_c, _ = Consultation.objects.filter(
                notes__startswith='[SIM]'
            ).delete()
            deleted_p, _ = MedicationPrescription.objects.filter(
                duration='7 days'
            ).delete()
            self.stdout.write(self.style.WARNING(
                f'Cleared {deleted_c} simulated consultations, {deleted_p} prescriptions.'
            ))

        # ── 3. Ensure inventory is adequate (bump to 2000 per medication) ────
        self._ensure_inventory(today)

        # ── 4. Pick PDL profiles to simulate ─────────────────────────────────
        # Prefer generated profiles; skip those already fully simulated
        already_simulated_pdl_ids = set(
            Consultation.objects
            .filter(notes__startswith='[SIM]')
            .values_list('pdl_profile_id', flat=True)
            .distinct()
        )

        candidates = list(
            PDLProfile.objects
            .exclude(id__in=already_simulated_pdl_ids)
            .order_by('?')[:count]
        )

        if not candidates:
            self.stdout.write(self.style.WARNING('No eligible PDL profiles found.'))
            return

        # ── 5. Build slot allocator pre-loaded from DB ───────────────────────
        allocator = SlotAllocator(physician)

        # ── 6. Simulate each PDL ─────────────────────────────────────────────
        sim_ok = sim_skip = 0
        consult_completed = consult_scheduled = prescription_count = 0

        for pdl in candidates:
            # Determine active health conditions
            active_conditions = list(
                HealthCondition.objects
                .filter(pdl_profile=pdl, is_active=True)
                .values_list('condition', flat=True)
            )
            condition_set = set(active_conditions)

            # Pick medication based on priority of condition
            med_name, dosage, frequency, duration_label, qty_7d = self._pick_medication(condition_set)
            medication = Medication.objects.filter(name=med_name).first()
            if not medication:
                self.stdout.write(self.style.WARNING(
                    f'  Medication "{med_name}" not in DB — skipping {pdl}'
                ))
                sim_skip += 1
                continue

            # ── Step 1: Initial consultation ─────────────────────────────────
            # Spread start dates: 14–90 days ago
            preferred_initial = today - timedelta(days=random.randint(14, 90))
            init_date, init_block, init_location = allocator.allocate(
                pdl, locations, preferred_initial
            )
            if not init_date:
                self.stdout.write(self.style.WARNING(
                    f'  No free initial slot for {pdl} — skipping.'
                ))
                sim_skip += 1
                continue

            init_vitals  = _gen_initial_vitals(condition_set)
            pmh_illnesses = self._build_pmh_illnesses(condition_set)
            tb_cough      = 'TB' in condition_set
            tb_exposure   = 'TB' in condition_set
            tb_prev_tx    = 'TB' in condition_set

            # Determine initial fr_conclusion
            if condition_set & {'HTN', 'DM', 'HEART', 'RENAL'}:
                init_conclusion    = 'PHILPEN'
                init_recommendation = 'DORM'
            elif condition_set & {'MENTAL'}:
                init_conclusion    = 'NEURO_PSYCH'
                init_recommendation = 'DORM'
            elif condition_set & {'TB', 'CANCER'}:
                init_conclusion    = 'SBIRT'
                init_recommendation = 'ISOLATED'
            else:
                init_conclusion    = 'HEALTHY'
                init_recommendation = 'DORM'

            cond_label_str = ', '.join(
                CONDITION_LABELS.get(c, c) for c in condition_set
            ) if condition_set else 'No chronic condition noted'

            initial_notes = (
                f'[SIM] Initial examination. Findings: {cond_label_str}. '
                f'Prescribed {med_name} {dosage} for 7 days.'
            )

            initial_consult = Consultation.objects.create(
                pdl_profile=pdl,
                physician=physician,
                location=init_location,
                reason=reason_initial,
                status=Consultation.Status.COMPLETED,
                consultation_date_date_only=init_date,
                consultation_time_block=init_block,
                is_an_emergency=False,
                notes=initial_notes,
                # Past medical history
                pmh_major_adult_illnesses=pmh_illnesses,
                pmh_alcohol_drinker=random.choice([True, False]),
                pmh_smoking=random.choice(['NEVER', 'CURRENT', 'STOPPED', 'PASSIVE']),
                # Physical exam on arrival
                **init_vitals,
                # Complaints based on condition
                pea_heart=(
                    'HEART' in condition_set or 'HTN' in condition_set
                ),
                pea_chest_lungs='ASTHMA' in condition_set,
                pea_general_appearance='MENTAL' in condition_set,
                # TB screening
                tb_unexplained_cough=tb_cough,
                tb_exposure=tb_exposure,
                tb_previous_treatment=tb_prev_tx,
                tb_bmi_less_18_5=(init_vitals['pea_bmi'] < 18.5),
                tb_remarks=(
                    'ONGOING_TB' if 'TB' in condition_set else None
                ),
                # Final remarks on initial visit
                fr_conclusion=init_conclusion,
                fr_recommendation=init_recommendation,
                fr_other_impressions=f'Prescribed {med_name} {dosage} {frequency} for {duration_label}.',
            )
            consult_completed += 1

            # ── Step 2: 7-day Prescription ───────────────────────────────────
            # Disable the auto-deduct by creating with quantity_dispensed=0 first,
            # then updating to avoid potential double-save deduction.
            prescription = MedicationPrescription(
                pdl_profile=pdl,
                medication=medication,
                dosage=dosage,
                frequency=frequency,
                duration=duration_label,
                prescribed_by=physician,
                quantity_prescribed=qty_7d,
                quantity_dispensed=0,          # set 0 first to avoid partial deduct
                dispensed_by=pharmacist,
                dispensed_at=None,
            )
            prescription.save()

            # Now set dispensed = prescribed → triggers full deduction once
            prescription.quantity_dispensed = qty_7d
            from django.utils import timezone as tz
            prescription.dispensed_at = tz.make_aware(
                __import__('datetime').datetime.combine(init_date, __import__('datetime').time(10, 0))
            )
            prescription.save()
            prescription_count += 1

            # ── Step 3: Follow-up consultation (7–10 days after initial) ─────
            followup_preferred = init_date + timedelta(days=random.randint(7, 10))
            fu_date, fu_block, fu_location = allocator.allocate(
                pdl, locations, followup_preferred, max_days=30
            )
            if not fu_date:
                self.stdout.write(self.style.WARNING(
                    f'  No free follow-up slot for {pdl} — skipping follow-up only.'
                ))
                sim_ok += 1
                continue

            fu_vitals = _gen_followup_vitals(condition_set, init_vitals)

            # Determine if follow-up is in the past or future
            if fu_date <= today:
                fu_status = Consultation.Status.COMPLETED
                # Determine outcome
                if condition_set & {'HTN', 'DM', 'HEART', 'RENAL', 'MENTAL'}:
                    fu_conclusion    = 'PHILPEN'
                    fu_recommendation = 'DORM'
                    fu_impressions   = (
                        f'Patient responded to {med_name}. Chronic condition requires '
                        'ongoing management. Continue medication as prescribed.'
                    )
                elif condition_set & {'TB'}:
                    fu_conclusion    = 'PHILPEN'
                    fu_recommendation = 'ISOLATED'
                    fu_impressions   = (
                        'Partial response to antibiotic therapy. Continue TB treatment protocol.'
                    )
                else:
                    fu_conclusion    = 'HEALTHY'
                    fu_recommendation = 'DORM'
                    fu_impressions   = (
                        f'Patient completed {med_name} course. Symptoms resolved. '
                        'No further medication required at this time.'
                    )
                consult_completed += 1
            else:
                # Follow-up is in the future → scheduled
                fu_status        = Consultation.Status.SCHEDULED
                fu_conclusion    = None
                fu_recommendation = None
                fu_impressions   = None
                # Use initial vitals as placeholders (not yet examined)
                fu_vitals = {}
                consult_scheduled += 1

            followup_notes = (
                f'[SIM] Follow-up after 7-day {med_name} course. '
                + (
                    'Patient reports improvement in symptoms.'
                    if fu_status == Consultation.Status.COMPLETED
                    else 'Pending follow-up examination.'
                )
            )

            Consultation.objects.create(
                pdl_profile=pdl,
                physician=physician,
                location=fu_location,
                reason=(
                    reason_medreview
                    if condition_set & {'HTN', 'DM', 'HEART'}
                    else reason_followup
                ),
                status=fu_status,
                consultation_date_date_only=fu_date,
                consultation_time_block=fu_block,
                is_an_emergency=False,
                notes=followup_notes,
                # Physical exam (improved vitals, if completed)
                **fu_vitals,
                # Final remarks (only if completed)
                fr_conclusion=fu_conclusion,
                fr_recommendation=fu_recommendation,
                fr_other_impressions=fu_impressions,
            )

            sim_ok += 1
            if sim_ok % 20 == 0:
                self.stdout.write(f'  ... {sim_ok} workflows simulated')

        # ── 7. Summary ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\nSimulation complete!\n'
            f'  PDL workflows simulated : {sim_ok}\n'
            f'  PDLs skipped            : {sim_skip}\n'
            f'  Consultations created   :\n'
            f'    Completed             : {consult_completed}\n'
            f'    Scheduled (future)    : {consult_scheduled}\n'
            f'  Prescriptions created   : {prescription_count}\n'
        ))

    # ── Helper methods ────────────────────────────────────────────────────────

    def _get_or_create_reason(self, reason: str, description: str):
        from consultations.models import ConsultationReason
        obj, _ = ConsultationReason.objects.get_or_create(
            reason=reason,
            defaults={'description': description},
        )
        return obj

    def _pick_medication(self, condition_set: set) -> tuple:
        """
        Return (med_name, dosage, frequency, duration, qty_7d).
        Priority order: HTN > DM > HEART > ASTHMA > TB > MENTAL > RENAL > CANCER > OTHER > fallback.
        """
        priority = ['HTN', 'DM', 'HEART', 'ASTHMA', 'TB', 'MENTAL', 'RENAL', 'CANCER', 'OTHER']
        for code in priority:
            if code in condition_set:
                return CONDITION_MED_MAP[code]
        return FALLBACK_MED

    def _build_pmh_illnesses(self, condition_set: set) -> str:
        """Build a Past Medical History string from active conditions."""
        labels = [CONDITION_LABELS.get(c, c) for c in condition_set]
        return ', '.join(labels) if labels else 'No significant past medical history.'

    def _ensure_inventory(self, today: date):
        """
        Make sure every medication in CONDITION_MED_MAP has at least 2000 units
        in stock so dispensation never drives inventory negative.
        """
        med_names = {v[0] for v in CONDITION_MED_MAP.values()} | {FALLBACK_MED[0]}
        for med_name in med_names:
            med = Medication.objects.filter(name=med_name).first()
            if not med:
                continue
            inv = MedicationInventory.objects.filter(medication=med).first()
            if inv:
                if inv.quantity < 2000:
                    inv.quantity = 2000
                    inv.save()
            else:
                # Create an inventory record if missing
                MedicationInventory.objects.create(
                    medication=med,
                    quantity=2000,
                    reorder_level=50,
                    expiration_date=today + timedelta(days=730),
                    location='Pharmacy Stockroom',
                )
        self.stdout.write('Inventory verified (all simulation medications >= 2000 units).')