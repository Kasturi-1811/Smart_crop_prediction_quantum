from django.db import models

# Create your models here.
from django.conf import settings



class FarmerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farmer_profile"
    )
    phone = models.CharField(max_length=15, blank=True)
    preferred_language = models.CharField(
        max_length=10,
        default="en"
    )
    village = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default="Andhra Pradesh")

    def __str__(self):
        return self.user.username