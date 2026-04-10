from django.db import models
# User model
from django.contrib.auth.models import User

# Create your models here.
class MedicalSpecialty(models.Model):
    """
    Model representing a medical specialty.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Medical Specialty"
        verbose_name_plural = "Medical Specialties"
        ordering = ['name']

class Physician(models.Model):
    """
    Model representing a doctor.
    """
    EMPLOYEE_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]

    username = models.ForeignKey(User, on_delete=models.CASCADE)
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPE_CHOICES, default='full_time')
    specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        specialty_str = f" ({self.specialty})" if self.specialty else ""
        return f"{self.username.first_name} {self.username.last_name}{specialty_str}"
    class Meta:
        verbose_name = "Physician"
        verbose_name_plural = "Physicians"
        ordering = ['username__last_name']


class ConsultationLocation(models.Model):
    """
    Model representing a consultation location.
    """
    room_number = models.CharField(max_length=10)
    capacity = models.IntegerField()

    def __str__(self):
        return self.room_number
    class Meta:
        verbose_name = "Consultation Location"
        verbose_name_plural = "Consultation Locations"
        ordering = ['room_number']

class ConsultationReason(models.Model):
    """
    Model representing a reason for consultation.
    """
    reason = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.reason
    class Meta:
        verbose_name = "Consultation Reason"
        verbose_name_plural = "Consultation Reasons"
        ordering = ['reason']

from pdl.models import PDLProfile
import enum

class ConsultationTimeBlock(enum.Enum):
    """
    Enum representing time 30-minute blocks for consultations, listed by start time.
    """
    BLOCK_08_00 = ("08:00", "8:00 AM")
    BLOCK_08_30 = ("08:30", "8:30 AM")
    BLOCK_09_00 = ("09:00", "9:00 AM")
    BLOCK_09_30 = ("09:30", "9:30 AM")
    BLOCK_10_00 = ("10:00", "10:00 AM")
    BLOCK_10_30 = ("10:30", "10:30 AM")
    BLOCK_11_00 = ("11:00", "11:00 AM")
    BLOCK_11_30 = ("11:30", "11:30 AM")
    BLOCK_13_00 = ("13:00", "1:00 PM")
    BLOCK_13_30 = ("13:30", "1:30 PM")
    BLOCK_14_00 = ("14:00", "2:00 PM")
    BLOCK_14_30 = ("14:30", "2:30 PM")
    BLOCK_15_00 = ("15:00", "3:00 PM")
    BLOCK_15_30 = ("15:30", "3:30 PM")
    BLOCK_16_00 = ("16:00", "4:00 PM")
    BLOCK_16_30 = ("16:30", "4:30 PM")
    BLOCK_17_00 = ("17:00", "5:00 PM")

    @classmethod
    def get_block_by_time(cls, time_str):
        """Get enum member by time string."""
        for block in cls:
            if block.value[0] == time_str:
                return block.name
        return None

    @classmethod
    def get_display_time(cls, block_name):
        """Get display time from block name."""
        try:
            return cls[block_name].value[1]
        except KeyError:
            return None

class Consultation(models.Model):
    """
    Model representing a consultation.
    """
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELED  = 'canceled',  'Canceled'

    pdl_profile = models.ForeignKey(PDLProfile, on_delete=models.CASCADE)
    physician = models.ForeignKey(Physician, on_delete=models.CASCADE)
    location = models.ForeignKey(ConsultationLocation, on_delete=models.CASCADE, blank=True, null=True)
    reason = models.ForeignKey(ConsultationReason, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    consultation_date_date_only = models.DateField(default=None)
    consultation_time_block = models.CharField(
        max_length=20, 
        choices=[(block.name, block.value[1]) for block in ConsultationTimeBlock],
        default=ConsultationTimeBlock.BLOCK_08_00.name  # Change this line
    )
    is_an_emergency = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    pmh_pediatric_history = models.TextField("Pediatric history", blank=True, null=True)
    pmh_major_adult_illnesses = models.TextField("Major adult illnesses", blank=True, null=True)
    pmh_major_surgeries = models.TextField("Major surgeries", blank=True, null=True)
    pmh_serious_injuries = models.TextField("Serious physical injuries", blank=True, null=True)
    pmh_limitations = models.TextField("Limitations on range of motion and activities", blank=True, null=True)
    pmh_medication_history = models.TextField("Medication history", blank=True, null=True)
    pmh_transfusions_reactions = models.TextField("History of transfusions/BT reactions", blank=True, null=True)
    pmh_mental_emotional = models.TextField("Mental and emotional problems", blank=True, null=True)

    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    pmh_blood_type = models.CharField("Blood type", max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)

    pmh_allergies = models.TextField("Allergies", blank=True, null=True)

    FAMILY_HISTORY_CHOICES = [
        ('HTN', 'Hypertension'),
        ('STROKE', 'Stroke'),
        ('MI', 'Heart attack'),
        ('DM', 'Diabetes'),
        ('ASTHMA', 'Asthma'),
        ('CKD', 'Kidney disease'),
        ('CA', 'Cancer'),
    ]
    pmh_family_history = models.CharField(
        "Family history",
        max_length=50,
        choices=FAMILY_HISTORY_CHOICES,
        blank=True,
        null=True,
        help_text="Select one family history condition"
    )

    pmh_psychiatric_history = models.BooleanField("Past psychiatric history", default=False)
    pmh_psychiatric_when = models.CharField("If yes, when", max_length=255, blank=True, null=True)
    pmh_psychiatric_facility = models.BooleanField("Confinement in a psychiatric facility", default=False)

    pmh_arv_treatment = models.BooleanField("ARV treatment", default=False)
    pmh_arv_details = models.TextField("ARV treatment details", blank=True, null=True)

    pmh_vaccines = models.TextField("Vaccines", blank=True, null=True)

    pmh_alcohol_drinker = models.BooleanField("Alcohol drinker", default=False)

    SMOKING_CHOICES = [
        ('NEVER', 'Never smoked'),
        ('CURRENT', 'Current smoker'),
        ('PASSIVE', 'Passive smoker'),
        ('STOPPED', 'Stopped > 1 year'),
    ]
    pmh_smoking = models.CharField("Smoking history", max_length=10, choices=SMOKING_CHOICES, blank=True, null=True)

    pmh_illicit_drugs = models.BooleanField("Use of illicit drugs", default=False)
    pmh_poly_drug_use = models.BooleanField("Uses more than one drug at a time", default=False)

    # --- Physical Examination on Arrival ---
    pea_temperature = models.DecimalField("Temperature (°C)", max_digits=4, decimal_places=1, blank=True, null=True)
    pea_blood_pressure = models.CharField("Blood pressure (mmHg)", max_length=20, blank=True, null=True)
    pea_heart_rate = models.IntegerField("Heart rate (bpm)", blank=True, null=True)
    pea_rr = models.IntegerField("Respiratory rate (breaths/min)", blank=True, null=True)
    pea_height = models.DecimalField("Height (cm)", max_digits=5, decimal_places=2, blank=True, null=True)
    pea_weight = models.DecimalField("Weight (kg)", max_digits=5, decimal_places=2, blank=True, null=True)
    pea_bmi = models.DecimalField("Body Mass Index (BMI)", max_digits=4, decimal_places=1, blank=True, null=True)

    pea_general_appearance = models.BooleanField("Complaining: General appearance", default=False)
    pea_head_eyes_ears_nose_throat = models.BooleanField("Complaining: Head/Eyes/Ears/Nose/Throat", default=False)
    pea_neck = models.BooleanField("Complaining: Neck", default=False)
    pea_chest_lungs = models.BooleanField("Complaining: Chest/Lungs", default=False)
    pea_heart = models.BooleanField("Complaining: Heart", default=False)
    pea_abdomen = models.BooleanField("Complaining: Abdomen", default=False)
    pea_genito_urinary = models.BooleanField("Complaining: Genito-urinary tract", default=False)
    pea_musculoskeletal = models.BooleanField("Complaining: Musculoskeletal system", default=False)
    pea_extremities = models.BooleanField("Complaining: Extremities", default=False)
    pea_other_findings = models.TextField("Other significant findings", blank=True, null=True)

        # --- TB Entry Screening Checklist ---
    tb_unexplained_cough = models.BooleanField("Unexplained cough", default=False)
    tb_bmi_less_18_5 = models.BooleanField("BMI < 18.5", default=False)
    tb_blood_streaked_sputum = models.BooleanField("Blood-streaked sputum", default=False)
    tb_cxr_suggestive = models.BooleanField("Chest X-ray suggestive of TB", default=False)
    tb_previous_treatment = models.BooleanField("History of previous TB treatment", default=False)
    tb_exposure = models.BooleanField("History of TB exposure", default=False)

    TB_REMARKS_CHOICES = [
        ('PRESUMPTIVE_TB', 'Presumptive TB'),
        ('PRESUMPTIVE_DR_TB', 'Presumptive DR-TB'),
        ('NOT_TB', 'Not TB'),
        ('ONGOING_TB', 'Ongoing TB'),
        ('OTHER_FU', 'Other follow-up'),
    ]
    tb_remarks = models.CharField(
        "TB remarks",
        max_length=20,
        choices=TB_REMARKS_CHOICES,
        blank=True,
        null=True
    )

    # --- Final Remarks ---
    FR_CONCLUSION_CHOICES = [
        ('HEALTHY', 'Practically healthy'),
        ('SBIRT', 'SBIRT'),
        ('PHILPEN', 'PhilPEN'),
        ('NEURO_PSYCH', 'Neuro-psychiatric evaluation'),
        ('ILL_TREATMENT', 'Further documentation of allegations of ill-treatment'),
    ]
    fr_conclusion = models.CharField(
        "Final conclusion",
        max_length=30,
        choices=FR_CONCLUSION_CHOICES,
        blank=True,
        null=True
    )

    fr_other_impressions = models.TextField(
        "Other impressions", blank=True, null=True
    )

    FR_RECOMMENDATION_CHOICES = [
        ('DORM', 'To be accommodated in general dormitory'),
        ('ISOLATED', 'To be isolated'),
        ('HOSPITAL', 'To be hospitalized'),
    ]
    fr_recommendation = models.CharField(
        "Recommendation",
        max_length=20,
        choices=FR_RECOMMENDATION_CHOICES,
        blank=True,
        null=True
    )

    # --- Follow-up Consultation Fields ---
    is_followup = models.BooleanField("Is a follow-up consultation", default=False)
    parent_consultation = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followups',
        verbose_name="Parent consultation"
    )
    followup_scheduled = models.BooleanField("Follow-up has been scheduled", default=False)
    followup_days = models.IntegerField("Days until follow-up", default=7)

    def __str__(self):
        # Consultation with Physician on Month Year, Time Block
        # lookup block name in enum
        block_name = self.consultation_time_block
        block_value = ConsultationTimeBlock[block_name].value[1]
        return f"Consultation with {self.physician} on {self.consultation_date_date_only.strftime('%d %B %Y')}"
    
    @property
    def consultation_time_block_display(self):
        """
        Returns the display value of the consultation time block.
        """
        return ConsultationTimeBlock[self.consultation_time_block].value[1]
    
    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        ordering = ['consultation_date_date_only', 'consultation_time_block']
        
        # PDL Consultation Constraints, make sure that a PDL Profile can only have one consultation per time block on the same date
        constraints = [
            models.UniqueConstraint(fields=['pdl_profile', 'consultation_date_date_only', 'consultation_time_block'], name='unique_consultation_per_pdl_per_time_block')
        ]
        # Physician Consultation Constraints, make sure that a Physician can only have one consultation per time block on the same date
        constraints += [
            models.UniqueConstraint(fields=['physician', 'consultation_date_date_only', 'consultation_time_block'], name='unique_consultation_per_physician_per_time_block')
        ]
        # Location Consultation Constraints, make sure that a Location can only have one consultation per time block on the same date
        constraints += [
            models.UniqueConstraint(fields=['location', 'consultation_date_date_only', 'consultation_time_block'], name='unique_consultation_per_location_per_time_block')
        ]
      