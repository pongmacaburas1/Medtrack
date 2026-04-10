from medications.models import (
    Pharmacist,
    MedicationType,
    MedicationGenericName,
    Medication,
    MedicationInventory,
    MedicationPrescription,
)
from pdl.models import PDLProfile
from consultations.models import Physician
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# PART 1: PHARMACISTS
pharmacists = [
    {"username": "pharmacist1", "employee_type": "full_time", "phone_number": "1234567890", "address": "123 Main St", "first_name": "John", "last_name": "Doe II"},
    {"username": "pharmacist2", "employee_type": "part_time", "phone_number": "9876543210", "address": "456 Elm St", "first_name": "Jane", "last_name": "Smith II"},
     {
        "username": "floigarcia",
        "first_name": "Floi Belen",
        "last_name": "Laquiores Garcia",
        "employee_type": "full_time", "phone_number": "1234567890", "address": "123 Main St"
    },
]

# Delete existing records
Pharmacist.objects.all().delete()

for pharmacist_data in pharmacists:
    user, created = User.objects.get_or_create(
        username=pharmacist_data["username"],
        defaults={"first_name": "Pharma", "last_name": "Cist", "email": f"{pharmacist_data['username']}@example.com"}
    )
    user.set_password("defaultpassword")
    user.save()
    pharmacist, created = Pharmacist.objects.get_or_create(
        username=user,
        defaults={
            "employee_type": pharmacist_data["employee_type"],
            "phone_number": pharmacist_data["phone_number"],
            "address": pharmacist_data["address"],
        }
    )
    if created:
        print(f"Added Pharmacist: {pharmacist.username}")
    else:
        print(f"Pharmacist already exists: {pharmacist.username}")

# PART 2: MEDICATION TYPES
medication_types = [
    {"name": "Antibiotic"},
    {"name": "Analgesic"},
    {"name": "Antidepressant"},
    {"name": "Antihistamine"},
    {"name": "Antipyretic"},
    {"name": "Antiseptic"},
    {"name": "Antiviral"},
    {"name": "Bronchodilator"},
    {"name": "Corticosteroid"},
    {"name": "Diuretic"},
    {"name": "Hormone"},
    {"name": "Immunosuppressant"},
    {"name": "Laxative"},
    {"name": "Muscle Relaxant"},
    {"name": "Narcotic"},
    {"name": "Sedative"},
    {"name": "Stimulant"},
    {"name": "Vasodilator"},
    {"name": "Vitamins and Minerals"},
    {"name": "Anticonvulsant"},
    {"name": "Antifungal"},
    {"name": "Antimalarial"},
    {"name": "Antiparasitic"},
    {"name": "Antipsychotic"},
    {"name": "Cardiovascular Agent"},
    {"name": "Gastrointestinal Agent"},
    {"name": "Neurological Agent"},
    {"name": "Respiratory Agent"},
    {"name": "Topical Agent"},
    {"name": "Miscellaneous"},
    {"name": "Cholesterol Care"},
    {"name": "Anticoagulant"},
    {"name": "Urology Agent"},
    {"name": "Pain Management"},
]

# Delete existing records
MedicationType.objects.all().delete()

for med_type_data in medication_types:
    med_type, created = MedicationType.objects.get_or_create(name=med_type_data["name"])
    if created:
        print(f"Added Medication Type: {med_type.name}")
    else:
        print(f"Medication Type already exists: {med_type.name}")

# PART 3: MEDICATION GENERIC NAMES
generic_names = [
    {"name": "Amoxicillin", "medication_type": "Antibiotic"},
    {"name": "Ibuprofen", "medication_type": "Analgesic"},
    {"name": "Sertraline", "medication_type": "Antidepressant"},
    {"name": "Loratadine", "medication_type": "Antihistamine"},
    {"name": "Diphenhydramine", "medication_type": "Antihistamine"},
    {"name": "Acetaminophen", "medication_type": "Antipyretic"},
    {"name": "Hydrocodone Bitartrate", "medication_type": "Narcotic"},
    {"name": "Levothyroxine Sodium", "medication_type": "Hormone"},
    {"name": "Amlodipine Besylate", "medication_type": "Cardiovascular Agent"},
    {"name": "Simvastatin", "medication_type": "Cholesterol Care"},
    {"name": "Omeprazole", "medication_type": "Gastrointestinal Agent"},
    {"name": "Gabapentin", "medication_type": "Neurological Agent"},
    {"name": "Sertraline Hydrochloride", "medication_type": "Antidepressant"},
    {"name": "Fluoxetine Hydrochloride", "medication_type": "Antidepressant"},
    {"name": "Cetirizine Hydrochloride", "medication_type": "Antihistamine"},
    {"name": "Montelukast Sodium", "medication_type": "Respiratory Agent"},
    {"name": "Tamsulosin Hydrochloride", "medication_type": "Urology Agent"},
    {"name": "Clopidogrel Bisulfate", "medication_type": "Cardiovascular Agent"},
    {"name": "Warfarin Sodium", "medication_type": "Anticoagulant"},
    {"name": "Atorvastatin Calcium", "medication_type": "Cholesterol Care"},
]

# Delete existing records
MedicationGenericName.objects.all().delete()

for generic_name_data in generic_names:
    med_type = MedicationType.objects.get(name=generic_name_data["medication_type"])
    generic_name, created = MedicationGenericName.objects.get_or_create(
        name=generic_name_data["name"],
        medication_type=med_type
    )
    if created:
        print(f"Added Medication Generic Name: {generic_name.name}")
    else:
        print(f"Medication Generic Name already exists: {generic_name.name}")

# PART 4: MEDICATIONS
medications = [
    {
        "name": "Amoxil",
        "generic_name": "Amoxicillin",
        "dosage_form": "tablet",
        "strength": "500mg",
        "route_of_administration": "oral",
        "manufacturer": "PharmaCorp",
    },
    {
        "name": "Advil",
        "generic_name": "Ibuprofen",
        "dosage_form": "capsule",
        "strength": "200mg",
        "route_of_administration": "oral",
        "manufacturer": "HealthCo",
    },
    {
        "name": "Zoloft",
        "generic_name": "Sertraline",
        "dosage_form": "tablet",
        "strength": "50mg",
        "route_of_administration": "oral",
        "manufacturer": "WellnessInc",
    },
    {
        "name": "Claritin",
        "generic_name": "Loratadine",
        "dosage_form": "tablet",
        "strength": "10mg",
        "route_of_administration": "oral",
        "manufacturer": "AllergyPharm",
    },
    {
        "name": "Tylenol",
        "generic_name": "Acetaminophen",
        "dosage_form": "tablet",
        "strength": "500mg",
        "route_of_administration": "oral",
        "manufacturer": "PainReliefCo",
    },
    {
        "name": "Hydrocodone",
        "generic_name": "Hydrocodone Bitartrate",
        "dosage_form": "tablet",
        "strength": "5mg/325mg",
        "route_of_administration": "oral",
        "manufacturer": "PainReliefCo",
    },

    {
        "name": "Levothyroxine",
        "generic_name": "Levothyroxine Sodium",
        "dosage_form": "tablet",
        "strength": "50mcg",
        "route_of_administration": "oral",
        "manufacturer": "ThyroidHealth",
    },
    {
        "name": "Amlodipine",
        "generic_name": "Amlodipine Besylate",
        "dosage_form": "tablet",
        "strength": "5mg",
        "route_of_administration": "oral",
        "manufacturer": "CardioPharm",
    },
    {
        "name": "Simvastatin",
        "generic_name": "Simvastatin",
        "dosage_form": "tablet",
        "strength": "20mg",
        "route_of_administration": "oral",
        "manufacturer": "CholesterolCare",
    },
    {
        "name": "Omeprazole",
        "generic_name": "Omeprazole",
        "dosage_form": "capsule",
        "strength": "20mg",
        "route_of_administration": "oral",
        "manufacturer": "GastroHealth",
    },
    {
        "name": "Gabapentin",
        "generic_name": "Gabapentin",
        "dosage_form": "capsule",
        "strength": "300mg",
        "route_of_administration": "oral",
        "manufacturer": "NeuroPharm",
    },
    {
        "name": "Sertraline",
        "generic_name": "Sertraline Hydrochloride",
        "dosage_form": "tablet",
        "strength": "50mg",
        "route_of_administration": "oral",
        "manufacturer": "MentalHealthCo",
    },
    {
        "name": "Fluoxetine",
        "generic_name": "Fluoxetine Hydrochloride",
        "dosage_form": "capsule",
        "strength": "20mg",
        "route_of_administration": "oral",
        "manufacturer": "MentalHealthCo",
    },
    {
        "name": "Cetirizine",
        "generic_name": "Cetirizine Hydrochloride",
        "dosage_form": "tablet",
        "strength": "10mg",
        "route_of_administration": "oral",
        "manufacturer": "AllergyPharm",
    },
    {
        "name": "Montelukast",
        "generic_name": "Montelukast Sodium",
        "dosage_form": "tablet",
        "strength": "10mg",
        "route_of_administration": "oral",
        "manufacturer": "RespiratoryHealth",
    },
    {
        "name": "Tamsulosin",
        "generic_name": "Tamsulosin Hydrochloride",
        "dosage_form": "capsule",
        "strength": "0.4mg",
        "route_of_administration": "oral",
        "manufacturer": "UrologyPharm",
    },
    {
        "name": "Clopidogrel",
        "generic_name": "Clopidogrel Bisulfate",
        "dosage_form": "tablet",
        "strength": "75mg",
        "route_of_administration": "oral",
        "manufacturer": "CardioPharm",
    },
    {
        "name": "Warfarin",
        "generic_name": "Warfarin Sodium",
        "dosage_form": "tablet",
        "strength": "5mg",
        "route_of_administration": "oral",
        "manufacturer": "AnticoagulantCo",
    },
    {
        "name": "Atorvastatin",
        "generic_name": "Atorvastatin Calcium",
        "dosage_form": "tablet",
        "strength": "10mg",
        "route_of_administration": "oral",
        "manufacturer": "CholesterolCare",
    },

]

# Delete existing records
Medication.objects.all().delete()

for medication_data in medications:
    generic_name = MedicationGenericName.objects.get(name=medication_data["generic_name"])
    medication, created = Medication.objects.get_or_create(
        name=medication_data["name"],
        generic_name=generic_name,
        defaults={
            "dosage_form": medication_data["dosage_form"],
            "strength": medication_data["strength"],
            "route_of_administration": medication_data["route_of_administration"],
            "manufacturer": medication_data["manufacturer"],
        }
    )
    if created:
        print(f"Added Medication: {medication.name}")
    else:
        print(f"Medication already exists: {medication.name}")

# PART 5: MEDICATION INVENTORY
inventory = [
    {"medication": "Amoxil", "quantity": 100, "expiration_date": datetime.now() + timedelta(days=365), "location": "Warehouse A"},
    {"medication": "Advil", "quantity": 200, "expiration_date": datetime.now() + timedelta(days=180), "location": "Warehouse B"},
    {"medication": "Zoloft", "quantity": 150, "expiration_date": datetime.now() + timedelta(days=90), "location": "Warehouse C"},
    {"medication": "Claritin", "quantity": 250, "expiration_date": datetime.now() + timedelta(days=30), "location": "Warehouse D"},
    {"medication": "Tylenol", "quantity": 300, "expiration_date": datetime.now() + timedelta(days=60), "location": "Warehouse E"},
    {"medication": "Hydrocodone", "quantity": 50, "expiration_date": datetime.now() + timedelta(days=120), "location": "Warehouse F"},
    {"medication": "Levothyroxine", "quantity": 80, "expiration_date": datetime.now() + timedelta(days=240), "location": "Warehouse G"},
    {"medication": "Amlodipine", "quantity": 120, "expiration_date": datetime.now() + timedelta(days=300), "location": "Warehouse H"},
    {"medication": "Simvastatin", "quantity": 90, "expiration_date": datetime.now() + timedelta(days=150), "location": "Warehouse I"},
    {"medication": "Omeprazole", "quantity": 110, "expiration_date": datetime.now() + timedelta(days=200), "location": "Warehouse J"},
    {"medication": "Gabapentin", "quantity": 130, "expiration_date": datetime.now() + timedelta(days=400), "location": "Warehouse K"},
    {"medication": "Sertraline", "quantity": 140, "expiration_date": datetime.now() + timedelta(days=50), "location": "Warehouse L"},
    {"medication": "Fluoxetine", "quantity": 160, "expiration_date": datetime.now() + timedelta(days=70), "location": "Warehouse M"},
    {"medication": "Cetirizine", "quantity": 170, "expiration_date": datetime.now() + timedelta(days=80), "location": "Warehouse N"},
    {"medication": "Montelukast", "quantity": 180, "expiration_date": datetime.now() + timedelta(days=90), "location": "Warehouse O"},
]

# Delete existing records
MedicationInventory.objects.all().delete()

for inventory_data in inventory:
    medication = Medication.objects.get(name=inventory_data["medication"])
    inventory_item, created = MedicationInventory.objects.get_or_create(
        medication=medication,
        defaults={
            "quantity": inventory_data["quantity"],
            "expiration_date": inventory_data["expiration_date"],
            "location": inventory_data["location"],
        }
    )
    if created:
        print(f"Added Inventory for Medication: {inventory_item.medication}")
    else:
        print(f"Inventory already exists for Medication: {inventory_item.medication}")

# PART 6: MEDICATION PRESCRIPTIONS
prescriptions = [
    {
        "pdl_profile": "johndoe",
        "medication": "Amoxil",
        "dosage": "500mg",
        "frequency": "3 times a day",
        "duration": "7 days",
        "prescribed_by": "floigarcia",
    },
    {
        "pdl_profile": "janesmith",
        "medication": "Advil",
        "dosage": "200mg",
        "frequency": "2 times a day",
        "duration": "5 days",
        "prescribed_by": "floigarcia",
    },
    {
        "pdl_profile": "johndoe",
        "medication": "Zoloft",
        "dosage": "50mg",
        "frequency": "once a day",
        "duration": "30 days",
        "prescribed_by": "floigarcia",
    },
    {
        "pdl_profile": "janesmith",
        "medication": "Claritin",
        "dosage": "10mg",
        "frequency": "once a day",
        "duration": "14 days",
        "prescribed_by": "floigarcia",
    },
    {
        "pdl_profile": "johndoe",
        "medication": "Tylenol",
        "dosage": "500mg",
        "frequency": "every 6 hours as needed",
        "duration": "3 days",
        "prescribed_by": "floigarcia",
    },
]

# Delete existing records
MedicationPrescription.objects.all().delete()

for prescription_data in prescriptions:
    pdl_profile = PDLProfile.objects.get(username__username=prescription_data["pdl_profile"])
    medication = Medication.objects.get(name=prescription_data["medication"])
    physician = Physician.objects.get(username__username=prescription_data["prescribed_by"])
    prescription, created = MedicationPrescription.objects.get_or_create(
        pdl_profile=pdl_profile,
        medication=medication,
        defaults={
            "dosage": prescription_data["dosage"],
            "frequency": prescription_data["frequency"],
            "duration": prescription_data["duration"],
            "prescribed_by": physician,
        }
    )
    if created:
        print(f"Added Prescription for: {prescription.pdl_profile}")
    else:
        print(f"Prescription already exists for: {prescription.pdl_profile}")