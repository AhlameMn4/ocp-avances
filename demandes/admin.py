from django.contrib import admin
from .models import Demande

@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display  = ['agent', 'event', 'gestionnaire', 'statut', 'date_saisie']
    list_filter   = ['statut', 'event__type_avance']
    search_fields = ['agent__matricule', 'agent__nom']
    readonly_fields = ['date_saisie']