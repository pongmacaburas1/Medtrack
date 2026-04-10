from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile (role=staff) whenever a new User is saved."""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': 'staff'},
        )