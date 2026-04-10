from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django_filters import FilterSet
from .filters import MedicationFilter
from .models import (
    Pharmacist,
    MedicationType,
    MedicationGenericName,
    Medication,
    MedicationInventory,
    MedicationPrescription,
)
from pdl.models import PDLProfile
from consultations.models import Physician, MedicalSpecialty



class PharmacistModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="pharmacist1", first_name="John", last_name="Doe Pharmacist")
        cls.pharmacist = Pharmacist.objects.create(
            username=cls.user,
            employee_type="full_time",
            phone_number="1234567890",
            address="123 Main St"
        )

    def test_pharmacist_creation(self):
        self.assertEqual(self.pharmacist.username.username, "pharmacist1")
        self.assertEqual(self.pharmacist.phone_number, "1234567890")
        self.assertEqual(self.pharmacist.address, "123 Main St")

    def test_pharmacist_str(self):
        self.assertEqual(str(self.pharmacist), "John Doe Pharmacist")


class MedicationTypeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medication_type = MedicationType.objects.create(name="Antibiotic")

    def test_medication_type_creation(self):
        self.assertEqual(self.medication_type.name, "Antibiotic")

    def test_medication_type_str(self):
        self.assertEqual(str(self.medication_type), "Antibiotic")


class MedicationGenericNameModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medication_type = MedicationType.objects.create(name="Antibiotic")
        cls.generic_name = MedicationGenericName.objects.create(
            name="Amoxicillin",
            medication_type=cls.medication_type
        )

    def test_generic_name_creation(self):
        self.assertEqual(self.generic_name.name, "Amoxicillin")
        self.assertEqual(self.generic_name.medication_type, self.medication_type)

    def test_generic_name_str(self):
        self.assertEqual(str(self.generic_name), "Amoxicillin")


class MedicationModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medication_type = MedicationType.objects.create(name="Antibiotic")
        cls.generic_name = MedicationGenericName.objects.create(
            name="Amoxicillin",
            medication_type=cls.medication_type
        )
        cls.medication = Medication.objects.create(
            name="Amoxil",
            generic_name=cls.generic_name,
            dosage_form="tablet",
            strength="500mg",
            route_of_administration="oral",
            manufacturer="PharmaCorp"
        )

    def test_medication_creation(self):
        self.assertEqual(self.medication.name, "Amoxil")
        self.assertEqual(self.medication.generic_name, self.generic_name)
        self.assertEqual(self.medication.dosage_form, "tablet")
        self.assertEqual(self.medication.strength, "500mg")
        self.assertEqual(self.medication.route_of_administration, "oral")
        self.assertEqual(self.medication.manufacturer, "PharmaCorp")

    def test_medication_str(self):
        self.assertEqual(str(self.medication), "Amoxil (Amoxicillin)")


class MedicationInventoryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medication_type = MedicationType.objects.create(name="Antibiotic")
        cls.generic_name = MedicationGenericName.objects.create(
            name="Amoxicillin",
            medication_type=cls.medication_type
        )
        cls.medication = Medication.objects.create(
            name="Amoxil",
            generic_name=cls.generic_name,
            dosage_form="tablet",
            strength="500mg",
            route_of_administration="oral",
            manufacturer="PharmaCorp"
        )
        cls.inventory = MedicationInventory.objects.create(
            medication=cls.medication,
            quantity=100,
            expiration_date=date(2024, 12, 31),
            location="Warehouse A"
        )

    def test_inventory_creation(self):
        self.assertEqual(self.inventory.medication, self.medication)
        self.assertEqual(self.inventory.quantity, 100)
        self.assertEqual(self.inventory.location, "Warehouse A")

    def test_inventory_str(self):
        self.assertEqual(str(self.inventory), "Amoxil (Amoxicillin) - 100 units")


class MedicationPrescriptionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_pdl = User.objects.create_user(username="janedoe", first_name="Jane", last_name="Doe")
        cls.pdl_profile = PDLProfile.objects.create(username=cls.user_pdl, phone_number="5551234567")

        cls.user_physician = User.objects.create_user(username="drsmithdoctor", first_name="John", last_name="Smith Doctor")
        cls.physician = Physician.objects.create(
            username=cls.user_physician,
            employee_type="full_time",
            specialty=MedicalSpecialty.objects.create(name="Cardiology", description="Heart-related medical specialty."),
            phone_number="1234567890",
            address="123 Main St"
        )

        cls.medication_type = MedicationType.objects.create(name="Antibiotic")
        cls.generic_name = MedicationGenericName.objects.create(
            name="Amoxicillin",
            medication_type=cls.medication_type
        )
        cls.medication = Medication.objects.create(
            name="Amoxil",
            generic_name=cls.generic_name,
            dosage_form="tablet",
            strength="500mg",
            route_of_administration="oral",
            manufacturer="PharmaCorp"
        )
        cls.prescription = MedicationPrescription.objects.create(
            pdl_profile=cls.pdl_profile,
            medication=cls.medication,
            dosage="500mg",
            frequency="3 times a day",
            duration="7 days",
            prescribed_by=cls.physician
        )

    def test_prescription_creation(self):
        self.assertEqual(self.prescription.pdl_profile, self.pdl_profile)
        self.assertEqual(self.prescription.medication, self.medication)
        self.assertEqual(self.prescription.dosage, "500mg")
        self.assertEqual(self.prescription.frequency, "3 times a day")
        self.assertEqual(self.prescription.duration, "7 days")
        self.assertEqual(self.prescription.prescribed_by, self.physician)

    def test_prescription_str(self):
        self.assertEqual(str(self.prescription), "Amoxil (Amoxicillin) prescribed to Jane Doe")

class MedicationListViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create sample data
        medication_type = MedicationType.objects.create(name="Antibiotic")
        generic_name = MedicationGenericName.objects.create(name="Amoxicillin", medication_type=medication_type)
        Medication.objects.create(name="Amoxicillin 500mg", generic_name=generic_name)
        Medication.objects.create(name="Amoxicillin 250mg", generic_name=generic_name)

    def test_medication_list_view(self):
        """
        Test the medication_list view to ensure it groups medications by their type, 
        verifies the presence of specific medications in the response, and checks 
        that medications are correctly grouped under their respective types.
        """
        client = self.client
        response = client.get(reverse('medications:medication_list'))

        self.assertEqual(response.status_code, 200)

        # Parse the response content
        content = response.content.decode('utf-8')

        # Check if the response contains grouped medication types
        self.assertIn("Antibiotic", content)
        self.assertIn("Amoxicillin 500mg", content)
        self.assertIn("Amoxicillin 250mg", content)

        # Ensure medications are grouped under their types
        self.assertTrue(content.index("Amoxicillin 500mg") > content.index("Antibiotic"))
        self.assertTrue(content.index("Amoxicillin 250mg") > content.index("Antibiotic"))
        



class MedicationFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create sample Medication objects for testing
        cls.medication_generic_name1 = MedicationGenericName.objects.create(
            name="Acetylsalicylic Acid",
            medication_type=MedicationType.objects.create(name="Analgesic")
        )
        cls.medication_generic_name2 = MedicationGenericName.objects.create(
            name="Ibuprofen",
            medication_type=MedicationType.objects.create(name="Anti-inflammatory")
        )
        cls.medication_generic_name3 = MedicationGenericName.objects.create(
            name="Acetaminophen",
            medication_type=MedicationType.objects.get_or_create(name="Analgesic")[0]
        )
        cls.med1 = Medication.objects.create(
            name="Aspirin",
            generic_name=cls.medication_generic_name1,
            dosage_form="Tablet",
            route_of_administration="Oral"
        )
        cls.med2 = Medication.objects.create(
            name="Ibuprofen",
            generic_name=cls.medication_generic_name2,
            dosage_form="Capsule",
            route_of_administration="Oral"
        )
        cls.med3 = Medication.objects.create(
            name="Tylenol",
            generic_name=cls.medication_generic_name3,
            dosage_form="Tablet",
            route_of_administration="Oral"
        )
    def test_filter_by_generic_name(self):
        # Ensure all test medications have the same route of administration
        self.assertEqual(self.med1.route_of_administration, "Oral")
        self.assertEqual(self.med2.route_of_administration, "Oral")
        self.assertEqual(self.med3.route_of_administration, "Oral")
        filter_data = {'generic_name': 'ibuprofen'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med2)

    def test_filter_case_insensitivity(self):
        filter_data = {'name': 'ASPIRIN'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med1)

    def test_filter_by_generic_name(self):
        filter_data = {'generic_name': 'ibuprofen'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med2)

    def test_filter_by_generic_name_partial_match(self):
        filter_data = {'generic_name': 'ibu'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med2)

    def test_filter_by_generic_name_case_insensitive(self):
        filter_data = {'generic_name': 'IBUPROFEN'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med2)

    def test_filter_by_generic_name(self):
        filter_data = {'generic_name': 'ibuprofen'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 1)
        self.assertEqual(filtered.qs.first(), self.med2)

    def test_filter_by_route_of_administration(self):
        filter_data = {'route_of_administration': 'Oral'}
        filtered = MedicationFilter(filter_data, queryset=Medication.objects.all())
        self.assertEqual(filtered.qs.count(), 3)
        self.assertIn(self.med1, filtered.qs)
        self.assertIn(self.med2, filtered.qs)
        self.assertIn(self.med3, filtered.qs)