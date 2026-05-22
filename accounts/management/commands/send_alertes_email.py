"""
Commande Django : envoyer les alertes email de clôture imminente.
À planifier via Windows Task Scheduler :
  python manage.py send_alertes_email
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from events.models import Event
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Envoie les alertes email pour les événements qui ferment dans 1 à 3 jours'

    def handle(self, *args, **kwargs):
        today   = timezone.now().date()
        ferment = Event.objects.filter(
            statut=Event.STATUT_ACTIF,
            date_fin__gte=today,
            date_fin__lte=today + timezone.timedelta(days=3),
        )

        if not ferment.exists():
            self.stdout.write(self.style.SUCCESS('Aucune alerte à envoyer.'))
            return

        admins = CustomUser.objects.filter(
            role=CustomUser.ROLE_ADMIN, actif=True
        ).exclude(email='')

        for ev in ferment:
            jours = (ev.date_fin - today).days
            label = "demain" if jours == 1 else f"dans {jours} jour(s)"
            sujet = f"[OCP Avances] ⚠ Clôture imminente : {ev} ({label})"
            corps = f"""Bonjour,

L'événement suivant sera automatiquement clôturé {label} :

  Type    : {ev.get_type_avance_display()}
  Année   : {ev.annee}
  Clôture : {ev.date_fin.strftime('%d/%m/%Y')}
  Demandes enregistrées : {ev.demandes.count()}

Connectez-vous à la plateforme pour consulter l'état de la campagne avant sa fermeture.

http://localhost:8000/events/{ev.pk}/detail/

Cordialement,
Système OCP Avances Sociales – Alerte automatique"""

            for admin in admins:
                try:
                    send_mail(
                        subject=sujet,
                        message=corps,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email],
                        fail_silently=False,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Alerte envoyée à {admin.email} – {ev}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Erreur email {admin.email}: {e}')
                    )