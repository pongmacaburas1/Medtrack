from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class DetentionStatus(models.Model):
    STATUS_CHOICES = [
        ("Under Investigation", "Under Investigation"),
        ("Released", "Released"),
        ("Transferred", "Transferred"),
        ("On Bail", "On Bail"),
        ("Escaped", "Escaped"),
    ]

    status = models.CharField("Status", max_length=100, choices=STATUS_CHOICES)
    description = models.TextField("Description", blank=True, null=True)

    def __str__(self):
        return self.status

    class Meta:
        verbose_name = _("Detention Status")
        verbose_name_plural = _("Detention Statuses")

class NameSuffix(models.TextChoices):
    NONE = "", _("(none)")
    JR   = "Jr.", "Jr."
    SR   = "Sr.", "Sr."
    II   = "II", "II"
    III  = "III", "III"
    IV   = "IV", "IV"
    MD   = "MD", "MD"
    PHD  = "PhD", "PhD"
    ESQ  = "Esq.", "Esq."


class PDLProfile(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(_("Phone Number"), max_length=15, blank=True, null=True)

    profile_picture_url = models.URLField(_("Profile Picture URL"), blank=True, null=True)

    middle_name = models.CharField(_("Middle Name(s)"), max_length=150, blank=True)
    name_suffix = models.CharField(
        _("Name Suffix"),
        max_length=10,
        choices=NameSuffix.choices,
        blank=True,
        default=NameSuffix.NONE,
        help_text=_("e.g., Jr., Sr., II, III; leave blank if none."),
    )

     # --- Choices ---
    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    CIVIL_STATUS_CHOICES = [
        ("S", "Single"),
        ("M", "Married"),
        ("W", "Widowed"),
        ("D", "Divorced"),
        ("SEP", "Separated"),
        ("LI", "Live-in / Domestic partnership"),
    ]

    EDUCATION_CHOICES = [
        ("NONE", "No formal schooling"),
        ("ELEM", "Elementary"),
        ("HS", "High School"),
        ("SHS", "Senior High School"),
        ("VOC", "Vocational/Technical"),
        ("COL", "College/Undergraduate"),
        ("POST", "Postgraduate"),
    ]

    # --- Fields with verbose_name ---
    sex = models.CharField(
        "Sex",
        max_length=1,
        choices=SEX_CHOICES,
        blank=True,
        null=True
    )
    age = models.PositiveSmallIntegerField(
        "Age",
        validators=[MinValueValidator(0), MaxValueValidator(120)],
        blank=True,
        null=True
    )
    civil_status = models.CharField(
        "Civil Status",
        max_length=3,
        choices=CIVIL_STATUS_CHOICES,
        blank=True,
        null=True
    )
    educational_attainment = models.CharField(
        "Educational Attainment",
        max_length=5,
        choices=EDUCATION_CHOICES,
        blank=True,
        null=True
    )
    date_of_birth = models.DateField("Date of Birth", blank=True, null=True)
    place_of_birth = models.CharField("Place of Birth", max_length=255, blank=True)

    place_of_birth_municipality = models.CharField("Municipality", max_length=128, blank=True)
    place_of_birth_province = models.CharField("Province", max_length=128, blank=True)
    place_of_birth_region = models.CharField("Region", max_length=128, blank=True)
    place_of_birth_country = models.CharField("Country", max_length=128, blank=True)

    date_of_commitment = models.DateField("Date of Commitment", blank=True, null=True)
    name_of_jail = models.CharField("Name of Jail", max_length=255, blank=True)

    case = models.CharField("Case", max_length=255, blank=True)
    case_number = models.CharField("Case Number", max_length=128, blank=True, db_index=True)

    origin_lockup = models.CharField("Origin Lockup", max_length=255, blank=True)

    contact_person_name = models.CharField("Name of Contact Person", max_length=255, blank=True)
    contact_person_address = models.TextField("Address of Contact Person", blank=True)
    contact_person_phone = models.CharField("Phone of Contact Person", max_length=64, blank=True)
    contact_person_email = models.EmailField("Email of Contact Person", blank=True)
    contact_person_relationship = models.CharField("Relationship to Contact Person", max_length=128, blank=True)




    def __str__(self):
        # build "First [Middle] Last"
        name = " ".join(
            p.strip() for p in [
                self.username.first_name,
                getattr(self, "middle_name", "") or "",
                self.username.last_name,
            ] if p
        )
        # append suffix as ", Jr." / ", III" if present
        return f"{name}, {self.name_suffix}" if getattr(self, "name_suffix", None) else name

    class Meta:
        verbose_name = _("PDL Profile")
        verbose_name_plural = _("PDL Profiles")


class DetentionReason(models.Model):
    REASON_CHOICES = [
        ("Theft", "Theft"),
        ("Assault", "Assault"),
        ("Drug Possession", "Drug Possession"),
        ("Fraud", "Fraud"),
        ("Vandalism", "Vandalism"),
    ]

    reason = models.CharField("Reason", max_length=255, choices=REASON_CHOICES)
    description = models.TextField("Description", blank=True, null=True)

    def __str__(self):
        return self.reason

    class Meta:
        verbose_name = "Detention Reason"
        verbose_name_plural = "Detention Reasons"


class UserRole(models.TextChoices):
    ADMIN       = 'admin',       'Admin'
    DOCTOR      = 'doctor',      'Doctor / Nurse'
    PHARMACIST  = 'pharmacist',  'Pharmacist'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.DOCTOR)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class HealthCondition(models.Model):
    CONDITION_CHOICES = [
        ('HTN',    'Hypertension'),
        ('DM',     'Diabetes Mellitus'),
        ('HEART',  'Heart Disease'),
        ('ASTHMA', 'Asthma / COPD'),
        ('TB',     'Tuberculosis'),
        ('MENTAL', 'Mental Health Condition'),
        ('RENAL',  'Kidney Disease'),
        ('CANCER', 'Cancer'),
        ('OTHER',  'Other'),
    ]

    pdl_profile   = models.ForeignKey(PDLProfile, on_delete=models.CASCADE, related_name='health_conditions')
    condition     = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    date_diagnosed = models.DateField(blank=True, null=True)
    notes         = models.TextField(blank=True)
    is_active     = models.BooleanField(default=True)
    recorded_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pdl_profile} — {self.get_condition_display()}"

    class Meta:
        verbose_name = "Health Condition"
        verbose_name_plural = "Health Conditions"
        ordering = ['-created_at']


class DetentionInstance(models.Model):
    pdl_profile = models.ForeignKey(
        PDLProfile, 
        on_delete=models.CASCADE, 
        related_name='detention_instances',
        verbose_name=_("PDL Profile")
    )
    detention_room_number = models.CharField(_("Detention Room Number"), max_length=50)
    detention_term_length = models.IntegerField(_("Detention Term Length"), default=0, blank=True, null=True)
    detention_status = models.ForeignKey(
        DetentionStatus, 
        on_delete=models.CASCADE, 
        related_name='detention_instances',
        verbose_name=_("Detention Status"),
        blank=True, null=True
    )
    detention_start_date = models.DateField(_("Detention Start Date"),blank=True, null=True)
    detention_end_date = models.DateField(_("Detention End Date"), blank=True, null=True)
    detention_reason = models.ForeignKey(
        DetentionReason, 
        on_delete=models.CASCADE, 
        related_name='detention_instances',
        verbose_name=_("Detention Reason"),
        blank=True, null=True
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"{self.pdl_profile} - {self.detention_status} - {self.detention_start_date}"
    
    class Meta:
        verbose_name = _("Detention Instance")
        verbose_name_plural = _("Detention Instances")
        ordering = ['-detention_start_date']

