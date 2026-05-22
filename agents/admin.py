from django.contrib import admin
from .models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display  = ['matricule', 'nom', 'prenom', 'service']
    list_filter   = ['service']
    search_fields = ['matricule', 'nom', 'prenom']
    # Read-only : aucune modification possible
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False