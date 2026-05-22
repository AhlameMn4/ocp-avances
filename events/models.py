from django.db import models
from django.utils import timezone


class Event(models.Model):
    TYPE_AID            = 'AID'
    TYPE_RENTREE        = 'RENTREE'
    TYPE_PREAMENAGEMENT = 'PREAMENAGEMENT'
    TYPE_CHOICES = [
        (TYPE_AID,            'Avance Aïd'),
        (TYPE_RENTREE,        'Avance Rentrée Scolaire'),
        (TYPE_PREAMENAGEMENT, 'Avance Pré-aménagement'),
    ]
    STATUT_ACTIF = 'ACTIF'
    STATUT_FERME = 'FERME'
    STATUT_CHOICES = [
        (STATUT_ACTIF, 'Actif'),
        (STATUT_FERME, 'Fermé'),
    ]

    type_avance  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_debut   = models.DateField()
    date_fin     = models.DateField()
    annee        = models.PositiveIntegerField()
    statut       = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_ACTIF)
    description  = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par     = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL,
                                     null=True, related_name='events_crees')

    class Meta:
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.get_type_avance_display()} {self.annee}"

    @property
    def est_actif(self):
        today = timezone.now().date()
        return self.statut == self.STATUT_ACTIF and self.date_debut <= today <= self.date_fin

    @property
    def jours_restants(self):
        return (self.date_fin - timezone.now().date()).days

    @property
    def pct_temps_ecoule(self):
        today = timezone.now().date()
        total = (self.date_fin - self.date_debut).days or 1
        ecoule = (today - self.date_debut).days
        return max(0, min(100, int(ecoule * 100 / total)))

    @property
    def couleur(self):
        if not self.est_actif:
            return 'secondary'
        jr = self.jours_restants
        if jr <= 2:  return 'danger'
        if jr <= 5:  return 'warning'
        return 'success'

    @property
    def logique(self):
        if self.type_avance == self.TYPE_PREAMENAGEMENT:
            return 'INCLUS', 'success', 'Les agents saisis bénéficient de cette avance.'
        return 'EXCLUS', 'danger', 'Les agents saisis sont exclus de cette avance.'

    @classmethod
    def fermer_expires(cls):
        from django.utils import timezone as tz
        today = tz.now().date()
        expires = cls.objects.filter(statut=cls.STATUT_ACTIF, date_fin__lt=today)
        ids = list(expires.values_list('id', flat=True))
        count = expires.update(statut=cls.STATUT_FERME)
        # Notifier les gestionnaires des événements fermés
        if ids:
            try:
                from accounts.models import Notification, CustomUser
                fermes = cls.objects.filter(id__in=ids)
                gestionnaires = CustomUser.objects.filter(
                    role=CustomUser.ROLE_GESTIONNAIRE, actif=True)
                for ev in fermes:
                    for g in gestionnaires:
                        Notification.envoyer(
                            destinataire=g,
                            type_notif=Notification.TYPE_EVENT_FERME,
                            titre=f"Campagne clôturée – {ev}",
                            message=(
                                f"La campagne « {ev.get_type_avance_display()} {ev.annee} » "
                                f"a été automatiquement clôturée le "
                                f"{ev.date_fin.strftime('%d/%m/%Y')}. "
                                f"La saisie n'est plus possible."
                            ),
                        )
            except Exception:
                pass
        return count