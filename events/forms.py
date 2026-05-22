from django import forms
from django.utils import timezone
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['type_avance', 'annee', 'date_debut', 'date_fin']
        widgets = {
            'type_avance': forms.Select(attrs={'class': 'form-select'}),
            'annee':       forms.NumberInput(attrs={
                'class': 'form-control', 'min': 2020, 'max': 2035
            }),
            'date_debut':  forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }, format='%Y-%m-%d'),
            'date_fin':    forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }, format='%Y-%m-%d'),
        }
        labels = {
            'type_avance': "Type d'avance",
            'annee':       'Année',
            'date_debut':  'Date de début',
            'date_fin':    'Date de fin',
        }

    def clean(self):
        cleaned = super().clean()
        debut = cleaned.get('date_debut')
        fin   = cleaned.get('date_fin')
        if debut and fin and fin <= debut:
            raise forms.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return cleaned