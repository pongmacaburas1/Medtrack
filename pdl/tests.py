from datetime import datetime, timedelta
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from .models import DetentionStatus, PDLProfile, DetentionReason, DetentionInstance
from .views import pdl_list
from consultations.models import Consultation, ConsultationReason, ConsultationLocation, Physician, MedicalSpecialty
from .filters import PDLFilter


class DetentionStatusModelTest(TestCase):
    def setUp(self):
        self.status = DetentionStatus.objects.create(
            status="In Custody",
            description="Currently detained in a facility."
        )

    def test_str_representation(self):
        self.assertEqual(str(self.status), "In Custody")

    def test_verbose_name(self):
        self.assertEqual(self.status._meta.verbose_name, "Detention Status")

    def test_verbose_name_plural(self):
        self.assertEqual(self.status._meta.verbose_name_plural, "Detention Statuses")


class PDLProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe",
            email="johndoe@email.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        self.pdl = PDLProfile.objects.create(
            username=self.user,
            phone_number="1234567890"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.pdl), "John Doe")



class DetentionReasonModelTest(TestCase):
    def setUp(self):
        self.reason = DetentionReason.objects.create(
            reason="Theft",
            description="Unlawful taking of another's property."
        )

    def test_str_representation(self):
        self.assertEqual(str(self.reason), "Theft")


class DetentionInstanceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="johndoe",
            first_name="John",
            last_name="Doe",
            email="johndoe@email.com",
            password="password123"
        )
        self.pdl = PDLProfile.objects.create(
            username=self.user,
            phone_number="1234567890"
        )
        self.status = DetentionStatus.objects.create(
            status="In Custody",
            description="Currently detained in a facility."
        )
        self.reason = DetentionReason.objects.create(
            reason="Theft",
            description="Unlawful taking of another's property."
        )
        self.instance = DetentionInstance.objects.create(
            pdl_profile=self.pdl,
            detention_term_length=30,
            detention_status=self.status,
            detention_start_date=datetime.now() - timedelta(days=10),
            detention_end_date=None,
            detention_reason=self.reason,
            notes="First offense."
        )

    def test_str_representation(self):
        self.assertEqual(
            str(self.instance),
            f"{self.pdl} - {self.status} - {self.instance.detention_start_date}"
        )

    def test_ordering(self):
        instances = DetentionInstance.objects.all()
        self.assertEqual(instances[0], self.instance)

class PDLListViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword', first_name='Test', last_name='User')
        self.user.save()

        self.user2 = User.objects.create_user(username='testphysician', password='testpassword', first_name='Test', last_name='Physician')
        self.user2.save()

        self.medical_specialty = MedicalSpecialty.objects.create(name="Cardiology", description="Heart-related issues")

        self.physician = Physician.objects.create(
            username=self.user2,
            phone_number="1234567890",
            specialty=self.medical_specialty,
        )
        # Create detention status and reason
        self.detention_status = DetentionStatus.objects.create(status="In Custody", description="Currently detained")
        self.detention_reason = DetentionReason.objects.create(reason="Theft", description="Unlawful taking of another's property")

        # Create PDL profiles and detention instances
        self.pdl_profile1 = PDLProfile.objects.create(username=self.user, phone_number="1234567890")
        self.detention_instance1 = DetentionInstance.objects.create(
            pdl_profile=self.pdl_profile1,
            detention_status=self.detention_status,
            detention_reason=self.detention_reason,
            detention_term_length=30,
            detention_start_date=datetime.now() - timedelta(days=10),
        )

        # Create consultations
        self.consultation_reason = ConsultationReason.objects.create(reason="Medical Checkup", description="Routine medical checkup")
        self.consultation_location = ConsultationLocation.objects.create(room_number="Room 101", capacity=5)
        self.consultation_instance = Consultation.objects.create(
            pdl_profile=self.pdl_profile1,
            physician=self.physician,
            status="scheduled",
            reason=self.consultation_reason,
            location=self.consultation_location,
            consultation_date_date_only=datetime.now() + timedelta(days=5))

    # def test_pdl_list_view(self):
    #     # Create a request
    #     request = self.factory.get(reverse('pdl:pdl_list'))

    #     # Call the view
    #     response = pdl_list(request)

    #     # Check response status
    #     self.assertEqual(response.status_code, 200)

class TestPDLFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data
        cls.user = User.objects.create(username="testuser", password="testpassword", first_name="Test", last_name="User")
        cls.profile = PDLProfile.objects.create(username=cls.user, phone_number="1234567890")
        cls.detention_status = DetentionStatus.objects.create(status="In Custody", description="Currently detained")
        cls.detention_reason = DetentionReason.objects.create(reason="Theft", description="Unlawful taking of another's property")
        cls.instance = DetentionInstance.objects.create(
            pdl_profile=cls.profile,
            detention_status=cls.detention_status,
            detention_reason=cls.detention_reason,
            detention_term_length=30,
            detention_start_date=datetime.now() - timedelta(days=10),
        )

    def test_filter_by_pdl_profile(self):
        filter_data = {'pdl_profile': 'testuser'}
        filtered = PDLFilter(filter_data, queryset=DetentionInstance.objects.all())
        self.assertIn(self.instance, filtered.qs)

    def test_filter_by_detention_status(self):
        filter_data = {'detention_status': self.detention_status}
        filtered = PDLFilter(filter_data, queryset=DetentionInstance.objects.all())
        self.assertIn(self.instance, filtered.qs)

    def test_filter_by_detention_reason(self):
        filter_data = {'detention_reason': self.detention_reason}
        filtered = PDLFilter(filter_data, queryset=DetentionInstance.objects.all())
        self.assertIn(self.instance, filtered.qs)

    def test_filter_combined(self):
        pdl_profile = PDLProfile.objects.get(username=self.user)
        filter_data = {
            'pdl_profile': pdl_profile.username,
            'detention_status': self.detention_status,
            'detention_reason': self.detention_reason,
        }
        filtered = PDLFilter(filter_data, queryset=DetentionInstance.objects.all())
        self.assertIn(self.instance, filtered.qs)