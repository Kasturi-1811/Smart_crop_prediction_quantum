
from django import forms
from .models import Farm


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = [
            "farm_name",
            "village",
            "district",
            "area_acres",
            "soil_type",
            "current_crop",
        ]
