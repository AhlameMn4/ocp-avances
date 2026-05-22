from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Crée le compte administrateur RH initial'

    def handle(self, *args, **kwargs):
        if CustomUser.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Le compte admin existe déjà.'))
            return
        CustomUser.objects.create_superuser(
            username='admin', email='admin@ocp.ma', password='Admin@OCP2025',
            first_name='Administrateur', last_name='RH',
            role=CustomUser.ROLE_ADMIN, actif=True,
            must_change_password=False,
        )
        self.stdout.write(self.style.SUCCESS(
            '✓ Admin créé : username=admin | password=Admin@OCP2025'
        ))