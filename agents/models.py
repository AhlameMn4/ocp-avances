from django.db import models


class Agent(models.Model):
    """Table Agent – lecture seule pour les gestionnaires.
    Seul l'admin peut ajouter des agents via l'interface dédiée."""

    matricule = models.CharField(max_length=20, primary_key=True)
    nom       = models.CharField(max_length=100)
    prenom    = models.CharField(max_length=100)
    service   = models.CharField(max_length=150)
    email     = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    poste     = models.CharField(max_length=100, blank=True, verbose_name="Poste / Fonction")
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='agents_ajoutes'
    )

    class Meta:
        verbose_name = "Agent"
        ordering    = ['service', 'nom', 'prenom']

    def __str__(self):
        return f"{self.matricule} – {self.nom} {self.prenom} ({self.service})"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def initiales(self):
        return f"{self.prenom[0]}{self.nom[0]}".upper()
