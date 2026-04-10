"""
Management command: generate_pdl_data
Generates 150 realistic Filipino PDL profiles with:
  - Demographics (sex, age, civil status, education)
  - Detention records (room, reason, status, dates)
  - Health conditions (hypertension, diabetes, heart disease, etc.)

Usage:
    python manage.py generate_pdl_data
    python manage.py generate_pdl_data --count 200
    python manage.py generate_pdl_data --clear   (wipe generated data first)
"""

import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from pdl.models import (
    DetentionInstance,
    DetentionReason,
    DetentionStatus,
    HealthCondition,
    PDLProfile,
)

# ---------------------------------------------------------------------------
# Name pools — realistic Filipino data
# ---------------------------------------------------------------------------

MALE_FIRST_NAMES = [
    "Juan", "Jose", "Antonio", "Eduardo", "Roberto", "Carlos", "Miguel",
    "Francisco", "Rodrigo", "Bernardo", "Dante", "Renato", "Ernesto",
    "Alfredo", "Rogelio", "Noel", "Rommel", "Arnel", "Gerry", "Wilfredo",
    "Reynaldo", "Rodel", "Mark", "Neil", "Jayson", "Bryan", "Jerome",
    "Kevin", "Christian", "John", "Michael", "Ryan", "Angelo", "Marco",
    "Paolo", "Diego", "Rafael", "Andres", "Ramon", "Enrique", "Lorenzo",
    "Alvin", "Dennis", "Gilbert", "Rolando", "Marlon", "Efren", "Nestor",
    "Felix", "Renaldo", "Virgilio", "Dexter", "Emilio", "Ferdinand",
    "Generoso", "Herminio", "Isidro", "Jaime", "Lino", "Modesto",
]

FEMALE_FIRST_NAMES = [
    "Maria", "Ana", "Elena", "Rosa", "Luz", "Remedios", "Corazon",
    "Maricel", "Lorna", "Nora", "Teresita", "Carmelita", "Esperanza",
    "Gloria", "Marites", "Jennifer", "Janine", "Jasmine", "Michelle",
    "Christine", "Lovely", "Marianne", "Kristine", "Clarissa", "Rowena",
    "Sheila", "Aileen", "Jocelyn", "Leonora", "Mylene", "Rosario",
    "Vilma", "Erlinda", "Florencia", "Genalyn", "Herminia", "Imelda",
    "Jovita", "Kathrina", "Lourdes", "Melinda", "Norma", "Ofelia",
    "Prescilla", "Quirina", "Soledad", "Tessie", "Ursula", "Veronica",
]

MIDDLE_NAMES = [
    "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Torres", "Flores",
    "Ramos", "Dela Cruz", "Mendoza", "Villanueva", "Castillo", "Aquino",
    "Pascual", "Aguilar", "Morales", "Rivera", "Evangelista", "Soriano",
    "Hernandez", "Diaz", "Gonzales", "Manalo", "Ocampo", "Concepcion",
    "Andrade", "Bacani", "Camacho", "Delos Reyes", "Figueroa",
]

LAST_NAMES = [
    "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Torres", "Flores",
    "Ramos", "Dela Cruz", "Mendoza", "Villanueva", "Castillo", "Aquino",
    "Pascual", "Aguilar", "Morales", "Rivera", "Evangelista", "Soriano",
    "Hernandez", "Diaz", "Gonzales", "Manalo", "Ocampo", "Concepcion",
    "Andrade", "Bacani", "Camacho", "Delos Reyes", "Figueroa", "Gutierrez",
    "Hidalgo", "Ibarra", "Jimenez", "Kalaw", "Lacson", "Macaraeg",
    "Navarro", "Ongpin", "Pimentel", "Quimpo", "Rufino", "Salazar",
    "Tan", "Umali", "Valencia", "Wenceslao", "Ybarra", "Zarate",
    "Alvarez", "Bernardo", "Corpuz", "Dimaculangan", "Estrada",
]

PROVINCES = [
    "Cebu", "Davao del Sur", "Pampanga", "Bulacan", "Laguna",
    "Cavite", "Rizal", "Batangas", "Pangasinan", "Iloilo",
    "Negros Occidental", "Leyte", "Zamboanga del Sur", "Misamis Oriental",
    "Albay", "Camarines Sur", "Quezon", "Nueva Ecija", "Tarlac", "Bataan",
]

MUNICIPALITIES = [
    "Cebu City", "Davao City", "Angeles City", "Malolos", "Santa Rosa",
    "Bacoor", "Antipolo", "Lipa City", "Dagupan", "Iloilo City",
    "Bacolod", "Tacloban", "Zamboanga City", "Cagayan de Oro",
    "Legazpi City", "Naga City", "Lucena City", "Cabanatuan",
    "Tarlac City", "Balanga",
]

JAIL_NAMES = [
    "Cebu City Jail",
    "Davao City Jail",
    "Manila City Jail",
    "Quezon City Jail",
    "Makati City Jail",
    "Caloocan City Jail",
    "Taguig City Jail",
    "Pasig City Jail",
    "Las Piñas City Jail",
    "Muntinlupa City Jail",
]

CRIME_DATA = [
    ("Murder", "Unlawful killing of a person with intent and premeditation."),
    ("Homicide", "Unlawful killing of a person without premeditation."),
    ("Robbery", "Taking property by force or threat of force."),
    ("Theft", "Unlawful taking of another's property."),
    ("Carnapping", "Theft or taking of a motor vehicle."),
    ("Rape", "Non-consensual sexual act committed by force or coercion."),
    ("Drug Possession", "Possession of illegal controlled substances."),
    ("Drug Trafficking", "Illegal sale, transport, or distribution of drugs."),
    ("Physical Injuries", "Inflicting bodily harm on another person."),
    ("Estafa / Swindling", "Deception or fraud for personal or financial gain."),
    ("Qualified Theft", "Theft with abuse of confidence or trust."),
    ("Illegal Firearms", "Possession of unlicensed or prohibited firearms."),
    ("Malversation", "Misappropriation of public funds by a public officer."),
    ("Kidnapping", "Unlawful detention or abduction of a person."),
    ("Arson", "Deliberate setting of fire to property."),
    ("Violation of RA 9165", "Violation of the Comprehensive Dangerous Drugs Act."),
    ("Violation of VAWC", "Violence against women and their children (RA 9262)."),
    ("Cattle Rustling", "Theft of livestock."),
    ("Illegal Gambling", "Operating or participating in illegal gambling activities."),
    ("Bribery", "Offering or accepting payment to influence official conduct."),
]

STATUS_NAMES = [
    "In Custody", "Released", "Transferred", "On Bail",
    "Escaped", "Under Investigation",
]

CONTACT_RELATIONSHIPS = [
    "Mother", "Father", "Spouse", "Sibling", "Child",
    "Cousin", "Aunt", "Uncle", "Friend", "Neighbor",
]

CONDITION_CODES = [c[0] for c in HealthCondition.CONDITION_CHOICES]

# Realistic probability weights for health conditions (per 100 detainees)
CONDITION_WEIGHTS = {
    "HTN":    30,   # Hypertension — very common
    "DM":     15,   # Diabetes
    "HEART":  10,   # Heart Disease
    "ASTHMA": 12,   # Asthma / COPD
    "TB":     20,   # TB — high in detention
    "MENTAL": 18,   # Mental health
    "RENAL":   6,   # Kidney disease
    "CANCER":  3,   # Cancer
    "OTHER":  10,   # Other
}

ROOM_NUMBERS = [
    "101", "102", "103", "104", "105",
    "201", "202", "203", "204", "205",
    "301", "302", "303", "304", "305",
    "A1", "A2", "A3", "B1", "B2", "B3",
    "C1", "C2", "D1", "D2",
]

EDUCATION_CHOICES = ["NONE", "ELEM", "HS", "SHS", "VOC", "COL", "POST"]
EDUCATION_WEIGHTS = [2, 20, 35, 10, 15, 15, 3]  # roughly realistic distribution

CIVIL_STATUS_CHOICES = ["S", "M", "W", "D", "SEP", "LI"]
CIVIL_WEIGHTS = [40, 35, 5, 5, 10, 5]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _weighted_choice(choices, weights):
    return random.choices(choices, weights=weights, k=1)[0]


def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _make_username(first: str, last: str, existing: set) -> str:
    base = (first + last).lower().replace(" ", "").replace("'", "")
    candidate = base
    suffix = 1
    while candidate in existing:
        candidate = f"{base}{suffix}"
        suffix += 1
    existing.add(candidate)
    return candidate


def _random_health_conditions(pdl_profile, admin_user, today: date) -> int:
    """Assign 0–3 health conditions to a PDL based on realistic probabilities."""
    assigned = 0
    for code, prob in CONDITION_WEIGHTS.items():
        # prob is "cases per 100 detainees"
        if random.randint(1, 100) <= prob:
            diag_date = _random_date(today - timedelta(days=1825), today)
            HealthCondition.objects.create(
                pdl_profile=pdl_profile,
                condition=code,
                date_diagnosed=diag_date,
                is_active=random.choices([True, False], weights=[85, 15])[0],
                notes="",
                recorded_by=admin_user,
            )
            assigned += 1
    return assigned


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Generate 100–200 realistic Filipino PDL profiles for demonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=150,
            help="Number of PDL profiles to generate (default: 150)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all previously generated PDL profiles before creating new ones.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        do_clear = options["clear"]
        today = date.today()

        # ── 0. Ensure lookup data exists ─────────────────────────────────────
        self._ensure_lookup_data()

        # ── 1. Optionally clear generated profiles ───────────────────────────
        if do_clear:
            generated = User.objects.filter(username__startswith="pdl_gen_")
            deleted, _ = generated.delete()
            self.stdout.write(self.style.WARNING(
                f"Cleared {deleted} previously generated user/profile records."
            ))

        # ── 2. Get or create a reference admin user ───────────────────────────
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True},
        )

        # ── 3. Load lookup objects ────────────────────────────────────────────
        statuses  = list(DetentionStatus.objects.all())
        reasons   = list(DetentionReason.objects.all())
        in_custody = DetentionStatus.objects.filter(status="In Custody").first()

        if not statuses or not reasons:
            self.stdout.write(self.style.ERROR(
                "Lookup data missing. Run: python manage.py initialize first."
            ))
            return

        # ── 4. Determine sex distribution (roughly 70 % male, 30 % female) ───
        male_count   = int(count * 0.70)
        female_count = count - male_count

        profiles_spec = (
            [("M", n) for n in random.sample(MALE_FIRST_NAMES * 5, male_count)]
            + [("F", n) for n in random.sample(FEMALE_FIRST_NAMES * 5, female_count)]
        )
        random.shuffle(profiles_spec)

        existing_usernames: set = set(User.objects.values_list("username", flat=True))

        # ── 5. Create profiles ────────────────────────────────────────────────
        created_count = 0
        condition_count = 0

        for sex, first_name in profiles_spec:
            last_name   = random.choice(LAST_NAMES)
            middle_name = random.choice(MIDDLE_NAMES)
            username    = _make_username(f"pdl_gen_{first_name}", last_name, existing_usernames)

            # Age: 18–65, weighted toward 25–45
            age = random.choices(
                range(18, 66),
                weights=[
                    max(1, 10 - abs(i - 32))  # bell-ish curve around 32
                    for i in range(18, 66)
                ],
                k=1
            )[0]
            dob = today - timedelta(days=age * 365 + random.randint(0, 364))

            # Create Django User
            user = User.objects.create_user(
                username=username,
                password="medtrack2024!",
                first_name=first_name,
                last_name=last_name,
                email=f"{username}@jail.gov.ph",
            )

            province    = random.choice(PROVINCES)
            municipality = random.choice(MUNICIPALITIES)
            jail_name   = random.choice(JAIL_NAMES)

            # Create PDLProfile
            pdl = PDLProfile.objects.create(
                username=user,
                middle_name=middle_name,
                sex=sex,
                age=age,
                civil_status=_weighted_choice(CIVIL_STATUS_CHOICES, CIVIL_WEIGHTS),
                educational_attainment=_weighted_choice(EDUCATION_CHOICES, EDUCATION_WEIGHTS),
                date_of_birth=dob,
                place_of_birth=f"{municipality}, {province}",
                place_of_birth_municipality=municipality,
                place_of_birth_province=province,
                place_of_birth_region="Region " + str(random.randint(1, 13)),
                place_of_birth_country="Philippines",
                name_of_jail=jail_name,
                case=random.choice([c[0] for c in CRIME_DATA]),
                case_number=f"CC-{random.randint(1000, 9999)}-{today.year}",
                origin_lockup=f"Cell {random.choice(ROOM_NUMBERS)}",
                contact_person_name=f"{random.choice(FEMALE_FIRST_NAMES)} {last_name}",
                contact_person_relationship=random.choice(CONTACT_RELATIONSHIPS),
                contact_person_phone=f"09{random.randint(100000000, 999999999)}",
            )

            # Detention start: 1–730 days ago
            det_start = today - timedelta(days=random.randint(1, 730))
            det_term  = random.choice([30, 60, 90, 120, 180, 365, 730])

            # 80 % still in custody
            if random.randint(1, 100) <= 80:
                det_status = in_custody or statuses[0]
                det_end    = None
            else:
                det_status = random.choice([s for s in statuses if s.status != "In Custody"])
                det_end    = det_start + timedelta(days=det_term)

            crime_name, crime_desc = random.choice(CRIME_DATA)
            det_reason, _ = DetentionReason.objects.get_or_create(
                reason=crime_name,
                defaults={"description": crime_desc},
            )

            DetentionInstance.objects.create(
                pdl_profile=pdl,
                detention_room_number=random.choice(ROOM_NUMBERS),
                detention_term_length=det_term,
                detention_status=det_status,
                detention_start_date=det_start,
                detention_end_date=det_end,
                detention_reason=det_reason,
            )

            # Assign health conditions
            condition_count += _random_health_conditions(pdl, admin_user, today)
            created_count += 1

            if created_count % 25 == 0:
                self.stdout.write(f"  ... {created_count}/{count} profiles created")

        # ── 6. Summary ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {created_count} PDL profiles "
            f"with {condition_count} health condition records."
        ))
        self.stdout.write(
            f"  Male:   {male_count}    Female: {female_count}\n"
            f"  Total health conditions assigned: {condition_count}\n"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ensure_lookup_data(self):
        """Create detention statuses and reasons if they don't exist yet."""
        for name, desc in [
            ("In Custody",           "Currently detained in a facility."),
            ("Released",             "No longer in custody."),
            ("Transferred",          "Moved to another facility or jurisdiction."),
            ("On Bail",              "Released temporarily on bail."),
            ("Escaped",              "Unlawfully left custody."),
            ("Under Investigation",  "Being investigated but not yet detained."),
        ]:
            DetentionStatus.objects.get_or_create(status=name, defaults={"description": desc})

        for name, desc in CRIME_DATA:
            DetentionReason.objects.get_or_create(reason=name, defaults={"description": desc})

        self.stdout.write("Lookup data verified.")