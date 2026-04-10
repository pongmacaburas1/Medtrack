# PART 1: MEDICAL SPECIALTIES

from consultations.models import MedicalSpecialty, ConsultationTimeBlock
from consultations.models import Physician
from django.contrib.auth.models import User
from pdl.models import PDLProfile
from consultations.models import Consultation
from datetime import datetime, timedelta

import numpy as np
from consultations.models import ConsultationReason

# Suggested medical specialties
medical_specialties = [
    {"name": "Cardiology", "description": "Study and treatment of heart conditions."},
    {"name": "Dermatology", "description": "Study and treatment of skin conditions."},
    {"name": "Neurology", "description": "Study and treatment of nervous system disorders."},
    {"name": "Pediatrics", "description": "Medical care for infants, children, and adolescents."},
    {"name": "Psychiatry", "description": "Study and treatment of mental health disorders."},
    {"name": "Orthopedics", "description": "Study and treatment of musculoskeletal system."},
    {"name": "Oncology", "description": "Study and treatment of cancer."},
    {"name": "Gastroenterology", "description": "Study and treatment of digestive system disorders."},
    {"name": "Endocrinology", "description": "Study and treatment of hormonal disorders."},
    {"name": "Ophthalmology", "description": "Study and treatment of eye disorders."},
    {"name": 'JO1 Registered Nurse', "description": "JO1 Registered Nurse"}
]

# Delete existing records
MedicalSpecialty.objects.all().delete()
# Populate the database
for specialty_data in medical_specialties:
    specialty, created = MedicalSpecialty.objects.get_or_create(
        name=specialty_data["name"],
        defaults={"description": specialty_data["description"]}
    )
    if created:
        print(f"Added medical specialty: {specialty.name}")
    else:
        print(f"Medical specialty already exists: {specialty.name}")


# PART 2: PHYSICIANS
# Suggested physicians
physicians = [
    {
        "username": "floigarcia",
        "first_name": "Floi Belen",
        "last_name": "Laquiores Garcia",
        "employee_type": "contract",
        "specialty": MedicalSpecialty.objects.get(name="JO1 Registered Nurse"),
        "phone_number": "555-4321",
        "email": "floigarcia@email.com",
        "address": "321 Pine St, Springfield"
    },
]
# Delete existing records
Physician.objects.all().delete()

for physician_data in physicians:
    user, created = User.objects.get_or_create(
        username=physician_data["username"],
        defaults={
            "first_name": physician_data["first_name"],
            "last_name": physician_data["last_name"],
            "email": physician_data["email"]
        }
    )
    user.set_password("defaultpassword")  # Set a default password
    user.save()  # Save the user instance
    if created:
        print(f"Added User profile: {user.username}")
    else:
        print(f"User profile already exists: {user.username}")

    # Create Physician
    physician, created = Physician.objects.get_or_create(
        username=user,
        defaults={
            "employee_type": physician_data["employee_type"],
            "specialty": physician_data["specialty"],
            "phone_number": physician_data["phone_number"],
            "address": physician_data["address"],
        }
    )

    if created:
        print(f"Added Physician profile for: {physician.username}")
        physician.save()  # Save the Physician instance
    else:
        print(f"Physician profile already exists for: {physician.username}")

# PART 3: CONSULTATION REASONS

# Suggested consultation reasons
consultation_reasons = [
    {"reason": "Routine Checkup", "description": "General health checkup."},
    {"reason": "Follow-up Visit", "description": "Follow-up on previous condition."},
    {"reason": "Emergency Consultation", "description": "Immediate medical attention required."},
    {"reason": "Specialist Referral", "description": "Referral to a specialist."},
    {"reason": "Medication Review", "description": "Review of current medications."},
]

# Delete existing records
ConsultationReason.objects.all().delete()

# Populate the database
for reason_data in consultation_reasons:
    reason, created = ConsultationReason.objects.get_or_create(
        reason=reason_data["reason"],
        defaults={"description": reason_data["description"]}
    )
    if created:
        print(f"Added consultation reason: {reason.reason}")
    else:
        print(f"Consultation reason already exists: {reason.reason}")


# PART 4: CONSULTATION LOCATIONS
from consultations.models import ConsultationLocation

# Suggested consultation locations
consultation_locations = [
    {"room_number": "RM101", "capacity": 2},
    {"room_number": "RM102", "capacity": 4},
    {"room_number": "RM103", "capacity": 3},
    {"room_number": "RM104", "capacity": 5},
    {"room_number": "RM105", "capacity": 6},
    {"room_number": "RM201", "capacity": 2},
    {"room_number": "RM202", "capacity": 4},
    {"room_number": "RM203", "capacity": 3},
    {"room_number": "RM204", "capacity": 5},
    {"room_number": "RM205", "capacity": 6}
]

# Delete existing records
ConsultationLocation.objects.all().delete()
# Populate the database
for location_data in consultation_locations:
    location, created = ConsultationLocation.objects.get_or_create(
        room_number=location_data["room_number"],
        defaults={"capacity": location_data["capacity"]}
    )
    if created:
        print(f"Added consultation location: {location.room_number}")
    else:
        print(f"Consultation location already exists: {location.room_number}")


# PART 5: CONSULTATIONS

consultations = [
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="johndoe")),
        "location": ConsultationLocation.objects.get(room_number="RM101"),
        "reason": ConsultationReason.objects.get(reason="Routine Checkup"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_08_00.name,  # Updated
        "notes": "Routine checkup for general health.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="chrisbrown")),
        "location": ConsultationLocation.objects.get(room_number="RM102"),
        "reason": ConsultationReason.objects.get(reason="Routine Checkup"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_09_30.name,  # Updated
        "notes": "Routine checkup for general health.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="lauragarcia")),
        "location": ConsultationLocation.objects.get(room_number="RM103"),
        "reason": ConsultationReason.objects.get(reason="Follow-up Visit"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_11_00.name,  # Updated
        "notes": "Follow-up on previous condition.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="lauragarcia")),
        "location": ConsultationLocation.objects.get(room_number="RM103"),
        "reason": ConsultationReason.objects.get(reason="Follow-up Visit"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_13_30.name,  # Updated
        "notes": "Follow-up on previous condition.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="emilydavis")),
        "location": ConsultationLocation.objects.get(room_number="RM103"),
        "reason": ConsultationReason.objects.get(reason="Follow-up Visit"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_14_30.name,  # Updated
        "notes": "Follow-up on previous condition.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="johndoe")),
        "location": ConsultationLocation.objects.get(room_number="RM104"),
        "reason": ConsultationReason.objects.get(reason="Emergency Consultation"),
        "status": "canceled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_15_00.name,  # Updated
        "notes": "Immediate medical attention required.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="johndoe")),
        "location": ConsultationLocation.objects.get(room_number="RM105"),
        "reason": ConsultationReason.objects.get(reason="Specialist Referral"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_13_00.name,  # Updated
        "notes": "Referral to a specialist.",
    },
    {
        "physician": Physician.objects.get(username=User.objects.get(username="floigarcia")),
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="chrisbrown")),
        "location": ConsultationLocation.objects.get(room_number="RM201"),
        "reason": ConsultationReason.objects.get(reason="Medication Review"),
        "status": "scheduled",
        "consultation_date_date_only": (datetime.now() + timedelta(days=np.random.randint(1, 10))).date(),
        "consultation_time_block": ConsultationTimeBlock.BLOCK_08_30.name,  # Updated
        "notes": "Review of current medications.",
    }
]
# Delete existing records
Consultation.objects.all().delete()

# Populate the database
for consultation_data in consultations:
    consultation, created = Consultation.objects.get_or_create(
        physician=consultation_data["physician"],
        pdl_profile=consultation_data["pdl_profile"],
        location=consultation_data["location"],
        reason=consultation_data["reason"],
        status=consultation_data["status"],
        consultation_date_date_only=consultation_data["consultation_date_date_only"],
        consultation_time_block=consultation_data["consultation_time_block"],
        defaults={
            "notes": consultation_data["notes"]
        }
    )
    if created:
        print(f"Added consultation: {consultation} with ID {consultation.id}")
    else:
        print(f"Consultation already exists: {consultation}")
