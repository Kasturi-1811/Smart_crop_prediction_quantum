from django.db import models

# Create your models here.

from django.conf import settings



class YieldPrediction(models.Model):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="yield_predictions",
    )

    crop = models.CharField(max_length=100)
    season = models.CharField(max_length=50)
    state = models.CharField(max_length=100)
    crop_year = models.IntegerField()
    area = models.FloatField()
    annual_rainfall = models.FloatField()

    classical_yield = models.FloatField()
    quantum_yield = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.crop} prediction - {self.created_at:%Y-%m-%d}"
