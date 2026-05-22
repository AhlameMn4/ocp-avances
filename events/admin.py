from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ['type_avance', 'annee', 'date_debut', 'date_fin', 'statut', 'cree_par']
    list_filter   = ['type_avance', 'statut', 'annee']
    search_fields = ['type_avance']