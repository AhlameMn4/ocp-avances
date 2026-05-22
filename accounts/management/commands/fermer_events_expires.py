"""
Commande Django : fermer automatiquement les événements expirés.
À planifier via Windows Task Scheduler (1x par jour à minuit) :
  python manage.py fermer_events_expires
"""
from django.core.management.base import BaseCommand
from events.models import Event


class Command(BaseCommand):
    help = 'Ferme automatiquement les événements dont la date de fin est dépassée'

    def handle(self, *args, **kwargs):
        count = Event.fermer_expires()
        if count:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {count} événement(s) clôturé(s) automatiquement.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('Aucun événement à clôturer.'))