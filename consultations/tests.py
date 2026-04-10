from datetime import date, timedelta
import datetime as dt
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils.timezone import now
from django.http import JsonResponse
from .views import consultation_time_block_list_api
from .models import ConsultationTimeBlock, ConsultationReason, ConsultationLocation

from .models import (
    Consultation,
    Physician,
    MedicalSpecialty,
    ConsultationLocation,
    ConsultationReason,
    ConsultationTimeBlock,
)
from .views import consultation_calendar
from .forms import ScheduleConsultationForm
from pdl.models import PDLProfile  # Ensure this is correctly imported or mocked


class PDLProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="janedoe", email="janedoe@example.com", first_name="Jane", last_name="Doe")
        self.pdl_profile = PDLProfile.objects.create(
            username=self.user,
            phone_number="5551234567"
        )

    def test_pdl_profile_creation(self):
        self.assertEqual(self.pdl_profile.username.username, "janedoe")
        self.assertEqual(self.pdl_profile.phone_number, "5551234567")

    def test_pdl_profile_str(self):
        self.assertEqual(str(self.pdl_profile), "Jane Doe")



class MedicalSpecialtyModelTest(TestCase):
    def setUp(self):
        self.specialty = MedicalSpecialty.objects.create(
            name="Cardiology",
            description="Heart-related medical specialty."
        )

    def test_medical_specialty_creation(self):
        self.assertEqual(self.specialty.name, "Cardiology")
        self.assertEqual(self.specialty.description, "Heart-related medical specialty.")

    def test_medical_specialty_str(self):
        self.assertEqual(str(self.specialty), "Cardiology")


class PhysicianModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="johndoe", email="johndoe@example.com", first_name="John", last_name="Doe")
        self.specialty = MedicalSpecialty.objects.create(name="Neurology", description="Brain-related specialty.")
        self.physician = Physician.objects.create(
            username=self.user,
            employee_type="full_time",
            specialty=self.specialty,
            phone_number="1234567890",
            address="123 Main St"
        )

    def test_physician_creation(self):
        self.assertEqual(self.physician.username.username, "johndoe")
        self.assertEqual(self.physician.specialty, self.specialty)

    def test_physician_str(self):
        self.assertEqual(str(self.physician), "John Doe (Neurology)")


class ConsultationLocationModelTest(TestCase):
    def setUp(self):
        self.location = ConsultationLocation.objects.create(
            room_number="101",
            capacity=10
        )

    def test_consultation_location_creation(self):
        self.assertEqual(self.location.room_number, "101")
        self.assertEqual(self.location.capacity, 10)

    def test_consultation_location_str(self):
        self.assertEqual(str(self.location), "101")


class ConsultationReasonModelTest(TestCase):
    def setUp(self):
        self.reason = ConsultationReason.objects.create(
            reason="Routine Checkup",
            description="A regular health checkup."
        )

    def test_consultation_reason_creation(self):
        self.assertEqual(self.reason.reason, "Routine Checkup")
        self.assertEqual(self.reason.description, "A regular health checkup.")

    def test_consultation_reason_str(self):
        self.assertEqual(str(self.reason), "Routine Checkup")


class ConsultationModelTest(TestCase):
    def setUp(self):
        self.user_physician = User.objects.create_user(username="alicesmith", email="alicesmith@example.com")
        self.user_pdl = User.objects.create_user(username="janedoe", email="janedoe@example.com")
        self.specialty = MedicalSpecialty.objects.create(name="Dermatology", description="Skin-related specialty.")
        self.physician = Physician.objects.create(
            username=self.user_physician,
            employee_type="part_time",
            specialty=self.specialty,
            phone_number="9876543210",
            address="456 Elm St"
        )
        self.location = ConsultationLocation.objects.create(room_number="202", capacity=5)
        self.reason = ConsultationReason.objects.create(reason="Skin Rash", description="Consultation for skin rash.")
        self.pdl_profile = PDLProfile.objects.create(
            username=self.user_pdl,
            phone_number="5551234567"
        )
                                    
        self.consultation = Consultation.objects.create(
            pdl_profile=self.pdl_profile,
            physician=self.physician,
            location=self.location,
            reason=self.reason,
            status="scheduled",
            consultation_date_date_only=dt.datetime(2025, 4, 5),
            consultation_time_block=ConsultationTimeBlock.BLOCK_17_00.name,  # Updated to use new enum name
            is_an_emergency=False,
            notes="Patient has mild symptoms."
        )

    def test_consultation_creation(self):
        self.assertEqual(self.consultation.physician, self.physician)
        self.assertEqual(self.consultation.location, self.location)
        self.assertEqual(self.consultation.reason, self.reason)
        self.assertEqual(self.consultation.status, "scheduled")
        self.assertEqual(self.consultation.consultation_date_date_only.strftime('%Y-%m-%d'), "2025-04-05")
        self.assertEqual(
            self.consultation.consultation_time_block, 
            ConsultationTimeBlock.BLOCK_17_00.name
        )
        self.assertFalse(self.consultation.is_an_emergency)
        self.assertEqual(self.consultation.notes, "Patient has mild symptoms.")

    def test_consultation_str(self):
        expected_time = ConsultationTimeBlock.BLOCK_17_00.value[1]  # "5:00 PM"
        self.assertEqual(
            str(self.consultation),
            f"Consultation with {self.physician} on {self.consultation.consultation_date_date_only.strftime('%d %B %Y')} at {expected_time} in {self.location.room_number}"
        )

    def test_unique_constraints(self):
        with self.assertRaises(IntegrityError):
            Consultation.objects.create(
                pdl_profile=self.pdl_profile,
                physician=self.physician,
                location=self.location,
                reason=self.reason,
                status="scheduled",
                consultation_date_date_only="2025-04-05",
                consultation_time_block=ConsultationTimeBlock.BLOCK_17_00.name,  # Updated
                is_an_emergency=False,
                notes="Duplicate consultation."
            )

class ScheduleConsultationViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword', first_name='Test', last_name='User')
        self.client.login(username='testuser', password='testpassword')

        # URL for the schedule consultation view
        self.url = reverse('consultations:schedule_consultation')

    def test_schedule_consultation_get(self):
        """
        Test that the schedule consultation page renders correctly with a GET request.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'consultations/schedule_consultation.html')
        self.assertIsInstance(response.context['form'], ScheduleConsultationForm)


    def test_schedule_consultation_post_invalid_data(self):

        """
        Test that an invalid POST request does not schedule a consultation.
        """
        invalid_data = {
            'physician': '',
            'consultation_date_date_only': '',
            'consultation_time_block': '',
            'status': '',
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertTemplateUsed(response, 'consultations/schedule_consultation.html')
        self.assertFalse(Consultation.objects.exists())  # No consultation should be created
        self.assertTrue(response.context['form'].errors)  # Form should have errors


class ScheduleConsultationFormTest(TestCase):
    def setUp(self):
        # Create test data for ConsultationLocation and ConsultationReason
        self.location = ConsultationLocation.objects.create(room_number="Test Location", capacity=5)
        self.reason = ConsultationReason.objects.create(reason="Test Reason", description="Test Description")
        self.consultation_time_block = ConsultationTimeBlock.BLOCK_08_00.name  # Updated

    def test_form_valid_data(self):
        form_data = {
            'consultation_date_date_only': (now() + timedelta(days=1)).date(),
            'consultation_time_block': ConsultationTimeBlock.BLOCK_09_00.name,  # Updated
            'location': self.location,
            'reason': self.reason,
            'is_an_emergency': False,
            'notes': 'Test notes',
        }
        form = ScheduleConsultationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        form_data = {
            'consultation_time_block': 'morning',
            'location': self.location.id,
            'reason': self.reason.id,
        }
        form = ScheduleConsultationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consultation_date_date_only', form.errors)

    def test_form_invalid_date(self):
        form_data = {
            'consultation_date_date_only': 'invalid-date',
            'consultation_time_block': 'morning',
            'location': self.location.id,
            'reason': self.reason.id,
            'is_an_emergency': False,
            'notes': 'Test notes',
        }
        form = ScheduleConsultationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consultation_date_date_only', form.errors)

    def test_form_invalid_location(self):
        form_data = {
            'consultation_date_date_only': (now() + timedelta(days=1)).date(),
            'consultation_time_block': 'morning',
            'location': 999,  # Invalid location ID
            'reason': self.reason.id,
            'is_an_emergency': False,
            'notes': 'Test notes',
        }
        form = ScheduleConsultationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('location', form.errors)

    def test_form_invalid_time_block(self):
        form_data = {
            'consultation_date_date_only': (now() + timedelta(days=1)).date(),
            'consultation_time_block': 'INVALID_BLOCK',  # Should be invalid
            'location': self.location.id,
            'reason': self.reason.id,
            'is_an_emergency': False,
            'notes': 'Test notes',
        }
        form = ScheduleConsultationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consultation_time_block', form.errors)

class ConsultationCalendarTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="testpassword", first_name="Test", last_name="User")
        self.user_pdl = User.objects.create_user(username="pdluser", password="testpassword", first_name="PDL", last_name="User")
        self.location = ConsultationLocation.objects.create(room_number="Test Room", capacity=5)
        self.reason = ConsultationReason.objects.create(reason="Test Reason", description="Test Description")
        self.pdl_profile = PDLProfile.objects.create(
            username=self.user_pdl,
            phone_number="5551234567"
        )

        self.physician_specialty = MedicalSpecialty.objects.create(
            name="General Practice",
            description="General medical practice."
        )
        self.physician = Physician.objects.create(
            username=self.user,
            employee_type="full_time",
            specialty=self.physician_specialty,
            phone_number="1234567890",
            address="123 Main St"

        )
        
        self.consultation1 = Consultation.objects.create(
            pdl_profile=self.pdl_profile,
            physician=self.physician,
            consultation_date_date_only=date(2023, 10, 15),
            status="scheduled",
            location=self.location,
            reason=self.reason,
        )
        self.consultation2 = Consultation.objects.create(
            pdl_profile=self.pdl_profile,
            physician=self.physician,
            consultation_date_date_only=date(2023, 10, 20),
            status="scheduled",
            location=self.location,
            reason=self.reason,
        )

    def test_consultation_calendar_current_month(self):
        request = self.factory.get('/?year=2023&month=10')
        consultations = Consultation.objects.all()
        context = consultation_calendar(request, consultations)

        self.assertEqual(context['year'], 2023)
        self.assertEqual(context['month'], 10)
        self.assertEqual(context['month_name'], "October")
        self.assertEqual(len(context['calendar_data'][2][6]['consultations']), 1)  # 15th is a Sunday
        self.assertEqual(len(context['calendar_data'][3][4]['consultations']), 1)  # 20th is a Friday

    def test_consultation_calendar_empty_month(self):
        request = self.factory.get('/?year=2023&month=11')
        consultations = Consultation.objects.all()
        context = consultation_calendar(request, consultations)

        self.assertEqual(context['year'], 2023)
        self.assertEqual(context['month'], 11)
        self.assertEqual(context['month_name'], "November")
        for week in context['calendar_data']:
            for day in week:
                self.assertEqual(len(day['consultations']), 0)  # No consultations in November


class ConsultationTimeBlockListAPITest(TestCase):
    def test_consultation_time_block_list_api(self):
        """
        Test the consultation_time_block_list_api view to ensure it returns
        the correct time blocks within office hours (08:00 to 17:00).
        """
        # Call the API endpoint
        response = self.client.get(reverse('consultations:consultation_time_block_list_api'))

        # Assert the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        time_blocks = response.json()

        # Assert the response is a list
        self.assertIsInstance(time_blocks, list)

        # Assert all time blocks are within office hours
        for block in time_blocks:
            self.assertIn('value', block)
            self.assertIn('display', block)
            time_value = ConsultationTimeBlock[block['value']].value[0]
            self.assertGreaterEqual(time_value, "08:00")
            self.assertLessEqual(time_value, "17:00")

    def test_time_block_enum_values(self):
        # Test a few specific time blocks
        self.assertEqual(ConsultationTimeBlock.BLOCK_08_00.value[1], "8:00 AM")
        self.assertEqual(ConsultationTimeBlock.BLOCK_13_30.value[1], "1:30 PM")
        self.assertEqual(ConsultationTimeBlock.BLOCK_17_00.value[1], "5:00 PM")

class ConsultationReasonListAPITest(TestCase):
    def setUp(self):
        # Create sample consultation reasons
        ConsultationReason.objects.create(reason="Reason 1", description="Description 1")
        ConsultationReason.objects.create(reason="Reason 2", description="Description 2")

    def test_consultation_reason_list_api(self):
        # Call the API endpoint
        response = self.client.get(reverse('consultations:consultation_reason_list_api'))

        # Assert the response status code
        self.assertEqual(response.status_code, 200)

        # Assert the response is a JSON response
        self.assertIsInstance(response, JsonResponse)

        # Parse the JSON response
        data = response.json()

        # Assert the response contains the correct number of reasons
        self.assertEqual(len(data), 2)

        # Assert the content of the response
        self.assertEqual(data[0]['reason'], "Reason 1")
        self.assertEqual(data[0]['description'], "Description 1")
        self.assertEqual(data[1]['reason'], "Reason 2")
        self.assertEqual(data[1]['description'], "Description 2")


class LocationListAPITestCase(TestCase):
    def setUp(self):
        # Create test data for ConsultationLocation
        ConsultationLocation.objects.create(id=1, room_number="101", capacity=10)
        ConsultationLocation.objects.create(id=2, room_number="102", capacity=10)
        ConsultationLocation.objects.create(id=3, room_number="103", capacity=10)

    def test_location_list_api(self):
        # Call the API endpoint
        response = self.client.get(reverse('consultations:location_list_api'))

        # Assert the response status code
        self.assertEqual(response.status_code, 200)

        # Assert the response data
        expected_data = [
            {'id': 1, 'room_number': "101"},
            {'id': 2, 'room_number': "102"},
            {'id': 3, 'room_number': "103"},
        ]
        self.assertJSONEqual(response.content, expected_data)

    