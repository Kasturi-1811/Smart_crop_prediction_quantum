from django.conf import settings
from django.db import models


class Farm(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms"
    )
    farm_name = models.CharField(max_length=100)
    village = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    area_acres = models.DecimalField(max_digits=10, decimal_places=2)
    soil_type = models.CharField(max_length=50, blank=True)
    current_crop = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.farm_name


class FarmEconomics(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="economics_records"
    )
    area_acres = models.DecimalField(max_digits=10, decimal_places=2)

    seed_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fertilizer_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labour_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    irrigation_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pesticide_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equipment_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    expected_yield_kg = models.DecimalField(max_digits=12, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2)

    total_cost = models.DecimalField(max_digits=14, decimal_places=2)
    revenue = models.DecimalField(max_digits=14, decimal_places=2)
    profit = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def profit_per_acre(self):
        return self.profit / self.area_acres if self.area_acres else 0

    def __str__(self):
        return f"{self.farm.farm_name} - Economics"