"""
Management command to add dummy consultation data for testing.
Creates sample consultations with Scheduled, Canceled, and Emergency statuses.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from consultations.models import Consultation, Physician, ConsultationLocation, ConsultationReason, ConsultationTimeBlock
from pdl.models import PDLProfile
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Add dummy consultation data with various statuses for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of consultations to create per status type (default: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get existing records
        pdl_profiles = list(PDLProfile.objects.all())
        physicians = list(Physician.objects.all())
        locations = list(ConsultationLocation.objects.all())
        reasons = list(ConsultationReason.objects.all())
        
        if not pdl_profiles:
            self.stdout.write(self.style.ERROR('No PDL profiles found. Please create PDL records first.'))
            return
            
        if not physicians:
            self.stdout.write(self.style.ERROR('No physicians found. Please create physician records first.'))
            return
            
        if not reasons:
            # Create default reasons if none exist
            default_reasons = [
                ('General Checkup', 'Routine health examination'),
                ('Follow-up', 'Follow-up consultation'),
                ('Emergency', 'Emergency medical situation'),
                ('Chronic Disease Management', 'Management of chronic conditions'),
                ('Mental Health', 'Mental health consultation'),
            ]
            for reason, desc in default_reasons:
                ConsultationReason.objects.get_or_create(reason=reason, defaults={'description': desc})
            reasons = list(ConsultationReason.objects.all())
            self.stdout.write(self.style.SUCCESS(f'Created {len(default_reasons)} default consultation reasons'))
        
        if not locations:
            # Create default locations if none exist
            for i in range(1, 4):
                ConsultationLocation.objects.get_or_create(room_number=f'Room {i}', defaults={'capacity': 5})
            locations = list(ConsultationLocation.objects.all())
            self.stdout.write(self.style.SUCCESS('Created 3 default consultation locations'))
        
        time_blocks = [block.name for block in ConsultationTimeBlock]
        today = date.today()
        
        created_counts = {'scheduled': 0, 'canceled': 0, 'emergency': 0}
        
        # Create SCHEDULED consultations (future dates)
        self.stdout.write('Creating scheduled consultations...')
        for i in range(count):
            future_date = today + timedelta(days=random.randint(1, 30))
            consultation = Consultation.objects.create(
                pdl_profile=random.choice(pdl_profiles),
                physician=random.choice(physicians),
                location=random.choice(locations) if locations else None,
                reason=random.choice(reasons),
                status='scheduled',
                consultation_date_date_only=future_date,
                consultation_time_block=random.choice(time_blocks),
                is_an_emergency=False,
                notes=f'Scheduled consultation #{i+1} - For routine checkup',
            )
            created_counts['scheduled'] += 1
        
        # Create CANCELED consultations (past dates)
        self.stdout.write('Creating canceled consultations...')
        cancel_reasons = [
            'Patient requested cancellation',
            'Doctor unavailable',
            'Schedule conflict',
            'Patient transferred to another facility',
            'Administrative cancellation',
        ]
        for i in range(count):
            past_date = today - timedelta(days=random.randint(1, 60))
            consultation = Consultation.objects.create(
                pdl_profile=random.choice(pdl_profiles),
                physician=random.choice(physicians),
                location=random.choice(locations) if locations else None,
                reason=random.choice(reasons),
                status='canceled',
                consultation_date_date_only=past_date,
                consultation_time_block=random.choice(time_blocks),
                is_an_emergency=False,
                notes=f'CANCELED: {random.choice(cancel_reasons)}',
            )
            created_counts['canceled'] += 1
        
        # Create EMERGENCY consultations (various dates)
        self.stdout.write('Creating emergency consultations...')
        emergency_notes = [
            'EMERGENCY: Severe chest pain reported',
            'EMERGENCY: High fever and difficulty breathing',
            'EMERGENCY: Injury requiring immediate attention',
            'EMERGENCY: Acute abdominal pain',
            'EMERGENCY: Severe allergic reaction',
            'EMERGENCY: Mental health crisis',
            'EMERGENCY: Suspected infection',
        ]
        for i in range(count):
            # Mix of past and recent dates
            random_date = today - timedelta(days=random.randint(0, 14))
            status = random.choice(['scheduled', 'completed'])  # Emergencies can be scheduled or completed
            consultation = Consultation.objects.create(
                pdl_profile=random.choice(pdl_profiles),
                physician=random.choice(physicians),
                location=random.choice(locations) if locations else None,
                reason=random.choice(reasons),
                status=status,
                consultation_date_date_only=random_date,
                consultation_time_block=random.choice(time_blocks),
                is_an_emergency=True,
                notes=random.choice(emergency_notes),
            )
            created_counts['emergency'] += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n=== Dummy Data Created Successfully ==='))
        self.stdout.write(self.style.SUCCESS(f'Scheduled consultations: {created_counts["scheduled"]}'))
        self.stdout.write(self.style.SUCCESS(f'Canceled consultations: {created_counts["canceled"]}'))
        self.stdout.write(self.style.SUCCESS(f'Emergency consultations: {created_counts["emergency"]}'))
        self.stdout.write(self.style.SUCCESS(f'Total: {sum(created_counts.values())} consultations'))
