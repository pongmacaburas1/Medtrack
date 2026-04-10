## part 1 : detention reasons

from pdl.models import DetentionReason

# suggested detention reasons
detention_reasons = [
    {"reason": "Theft", "description": "Unlawful taking of another's property."},
    {"reason": "Assault", "description": "Physical attack or threat of attack."},
    {"reason": "Drug Possession", "description": "Possession of illegal substances."},
    {"reason": "Fraud", "description": "Deception for personal or financial gain."},
    {"reason": "Vandalism", "description": "Deliberate destruction of property."},
    {"reason": "Trespassing", "description": "Unauthorized entry onto private property."},
    {"reason": "Domestic Violence", "description": "Violence or abuse within a household."},
    {"reason": "Public Intoxication", "description": "Being drunk in a public place."},
    {"reason": "Disorderly Conduct", "description": "Disruptive or offensive behavior in public."},
    {"reason": "Burglary", "description": "Illegal entry into a building with intent to commit a crime."},
]

# delete existing records
DetentionReason.objects.all().delete()

# populate the database
for reason_data in detention_reasons:
    reason, created = DetentionReason.objects.get_or_create(
        reason=reason_data["reason"],
        defaults={"description": reason_data["description"]}
    )
    if created:
        print(f"Added detention reason: {reason.reason}")
    else:
        print(f"Detention reason already exists: {reason.reason}")


## part 2 : detention types
from pdl.models import DetentionStatus

# suggested detention statuses
detention_statuses = [
    {"status": "In Custody", "description": "Currently detained in a facility."},
    {"status": "Released", "description": "No longer in custody."},
    {"status": "Transferred", "description": "Moved to another facility or jurisdiction."},
    {"status": "On Bail", "description": "Released temporarily on bail."},
    {"status": "Escaped", "description": "Unlawfully left custody."},
    {"status": "Under Investigation", "description": "Being investigated but not yet detained."},
]

# delete existing records
DetentionStatus.objects.all().delete()

# populate the database
for status_data in detention_statuses:
    status, created = DetentionStatus.objects.get_or_create(
        status=status_data["status"],
        defaults={"description": status_data["description"]}
    )
    if created:
        print(f"Added detention status: {status.status}")
    else:
        print(f"Detention status already exists: {status.status}")


## part 3 : pdl profiles

from pdl.models import PDLProfile
from django.contrib.auth.models import User

# suggested pdl profiles
pdl_users = [
    {"username": "johndoe", "email": "johndoe@email.com", "phone_number": "1234567890", "first_name": "John", "last_name": "Doe"},
    {"username": "janesmith", "email": "janesmith@email.com", "phone_number": "9876543210", "first_name": "Jane", "last_name": "Smith"},
    {"username": "michaeljohnson", "email": "michaeljohnson@email.com", "phone_number": "5551234567", "first_name": "Michael", "last_name": "Johnson"},
    {"username": "emilydavis", "email": "emilydavis@email.com", "phone_number": "4449876543", "first_name": "Emily", "last_name": "Davis"},
    {"username": "chrisbrown", "email": "chrisbrown@email.com", "phone_number": "3334567890", "first_name": "Chris", "last_name": "Brown"},
    {"username": "sarahwilson", "email": "sarahwilson@email.com", "phone_number": "2221239876", "first_name": "Sarah", "last_name": "Wilson"},
    {"username": "davidmartinez", "email": "davidmartinez@email.com", "phone_number": "1119876543", "first_name": "David", "last_name": "Martinez"},
    {"username": "lauragarcia", "email": "lauragarcia@email.com", "phone_number": "6667891234", "first_name": "Laura", "last_name": "Garcia"},
    {"username": "jamesanderson", "email": "jamesanderson@email.com", "phone_number": "7776543210", "first_name": "James", "last_name": "Anderson"},
    {"username": "oliviataylor", "email": "oliviataylor@email.com", "phone_number": "8881234567", "first_name": "Olivia", "last_name": "Taylor"},
    {"username": "danielthomas", "email": "danielthomas@email.com", "phone_number": "9999876543", "first_name": "Daniel", "last_name": "Thomas"},
]

# delete existing records
PDLProfile.objects.all().delete()
User.objects.filter(username__in=[user["username"] for user in pdl_users]).delete()

# populate the database
for pdl_data in pdl_users:
    user, created = User.objects.get_or_create(
        username=pdl_data["username"],

        defaults={"email": pdl_data["email"],
                    "first_name": pdl_data["first_name"],
                    "last_name": pdl_data["last_name"]}
    )
    user.set_password("defaultpassword")  # Set a default password
    user.save()  # Save the user instance
    if created:
        print(f"Added User profile: {user.username}")
    else:
        print(f"User profile already exists: {user.username}")

   # Create PDLProfile
    pdl_profile, created = PDLProfile.objects.get_or_create(
        username=user,
        defaults={"phone_number": pdl_data["phone_number"]}
    )

    if created:
        print(f"Added PDL profile for: {pdl_profile.username.username}")
        pdl_profile.save()  # Save the PDLProfile instance
    else:   
        print(f"PDL profile already exists for: {pdl_profile.username.username}")
    
## part 4 : detention instances
from pdl.models import DetentionInstance
from datetime import datetime, timedelta
import random

# suggested detention instances
detention_instances = [
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="johndoe")),
        "detention_term_length": 30,
        "detention_status": DetentionStatus.objects.get(status="In Custody"),
        "detention_start_date": datetime.now() - timedelta(days=10),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Theft"),
        'detention_room_number': "123",
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="janesmith")),
        "detention_term_length": 60,
        "detention_status": DetentionStatus.objects.get(status="Released"),
        "detention_start_date": datetime.now() - timedelta(days=70),
        "detention_end_date": datetime.now() - timedelta(days=10),
        "detention_reason": DetentionReason.objects.get(reason="Assault"),
        'detention_room_number': "456"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="michaeljohnson")),
        "detention_term_length": 90,
        "detention_status": DetentionStatus.objects.get(status="Transferred"),
        "detention_start_date": datetime.now() - timedelta(days=50),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Drug Possession"),
        'detention_room_number': "123"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="emilydavis")),
        "detention_term_length": 45,
        "detention_status": DetentionStatus.objects.get(status="On Bail"),
        "detention_start_date": datetime.now() - timedelta(days=20),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Fraud"),
        'detention_room_number': "144"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="chrisbrown")),
        "detention_term_length": 120,
        "detention_status": DetentionStatus.objects.get(status="Escaped"),
        "detention_start_date": datetime.now() - timedelta(days=150),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Vandalism"),
        'detention_room_number': "123"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="sarahwilson")),
        "detention_term_length": 15,
        "detention_status": DetentionStatus.objects.get(status="Under Investigation"),
        "detention_start_date": datetime.now() - timedelta(days=5),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Trespassing"),
        'detention_room_number': "123"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="davidmartinez")),
        "detention_term_length": 60,
        "detention_status": DetentionStatus.objects.get(status="In Custody"),
        "detention_start_date": datetime.now() - timedelta(days=30),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Domestic Violence"),
        'detention_room_number': "3278"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="lauragarcia")),
        "detention_term_length": 10,
        "detention_status": DetentionStatus.objects.get(status="Released"),
        "detention_start_date": datetime.now() - timedelta(days=15),
        "detention_end_date": datetime.now() - timedelta(days=5),
        "detention_reason": DetentionReason.objects.get(reason="Public Intoxication"),
        'detention_room_number': "1289"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="jamesanderson")),
        "detention_term_length": 25,
        "detention_status": DetentionStatus.objects.get(status="Transferred"),
        "detention_start_date": datetime.now() - timedelta(days=40),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Disorderly Conduct"),
        'detention_room_number': "12"
    },
    {
        "pdl_profile": PDLProfile.objects.get(username=User.objects.get(username="oliviataylor")),
        "detention_term_length": 90,
        "detention_status": DetentionStatus.objects.get(status="On Bail"),
        "detention_start_date": datetime.now() - timedelta(days=60),
        "detention_end_date": None,
        "detention_reason": DetentionReason.objects.get(reason="Burglary"),
        'detention_room_number': "129"
    },
]

# delete existing records
DetentionInstance.objects.all().delete()

# populate the database
for instance_data in detention_instances:
    instance, created = DetentionInstance.objects.get_or_create(
        pdl_profile=instance_data["pdl_profile"],
        detention_term_length=instance_data["detention_term_length"],
        detention_status=instance_data["detention_status"],
        detention_start_date=instance_data["detention_start_date"],
        detention_end_date=instance_data["detention_end_date"],
        detention_reason=instance_data["detention_reason"],
        detention_room_number=instance_data["detention_room_number"]

    )
    if created:
        print(f"Added detention instance for: {instance.pdl_profile.username}")
    else:
        print(f"Detention instance already exists for: {instance.pdl_profile.username}")