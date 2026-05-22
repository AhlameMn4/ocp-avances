from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ActionLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'role', 'actif', 'date_creation']
    list_filter   = ['role', 'actif']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('OCP', {'fields': ('role', 'service', 'actif', 'must_change_password')}),
    )


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display  = ['date_heure', 'utilisateur', 'type_action', 'description', 'ip_address']
    list_filter   = ['type_action']
    search_fields = ['utilisateur__username', 'description']
    readonly_fields = ['date_heure']