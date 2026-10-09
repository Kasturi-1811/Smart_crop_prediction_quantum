from django.db import models
from django.contrib.auth.models import User


class Listing(models.Model):
    CATEGORY_CHOICES = [
        ("seeds", "Seeds"),
        ("fertilizers", "Fertilizers"),
        ("pesticides", "Pesticides"),
        ("equipment", "Farm Equipment"),
        ("produce", "Crops and Produce"),
        ("other", "Other"),
    ]

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="marketplace_listings",
    )
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    contact = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title