from django.db import models


class Demande(models.Model):
    STATUT_INCLUS = 'INCLUS'
    STATUT_EXCLUS = 'EXCLUS'
    STATUT_CHOICES = [
        (STATUT_INCLUS, 'Inclus'),
        (STATUT_EXCLUS, 'Exclus'),
    ]

    agent        = models.ForeignKey('agents.Agent',        on_delete=models.PROTECT, related_name='demandes')
    event        = models.ForeignKey('events.Event',        on_delete=models.PROTECT, related_name='demandes')
    gestionnaire = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, related_name='demandes_saisies')
    statut       = models.CharField(max_length=10, choices=STATUT_CHOICES)
    date_saisie  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_saisie']
        constraints = [
            models.UniqueConstraint(fields=['agent', 'event'], name='unique_agent_event')
        ]

    def __str__(self):
        return f"{self.agent} – {self.event} [{self.statut}]"