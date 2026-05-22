from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_ADMIN        = 'admin'
    ROLE_GESTIONNAIRE = 'gestionnaire'
    ROLE_CHOICES = [
        (ROLE_ADMIN,        'Administrateur RH'),
        (ROLE_GESTIONNAIRE, 'Gestionnaire'),
    ]

    role                 = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_GESTIONNAIRE)
    service              = models.CharField(max_length=150, blank=True, verbose_name="Service")
    telephone            = models.CharField(max_length=20, blank=True)
    actif                = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)
    date_creation        = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilisateur"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_admin_rh(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_gestionnaire(self):
        return self.role == self.ROLE_GESTIONNAIRE

    @property
    def initiales(self):
        f = self.first_name[0].upper() if self.first_name else ''
        l = self.last_name[0].upper()  if self.last_name  else ''
        return (f + l) or self.username[0].upper()


class Notification(models.Model):
    TYPE_AGENT_AJOUTE  = 'AGENT_AJOUTE'
    TYPE_COMPTE_CREE   = 'COMPTE_CREE'
    TYPE_EVENT_OUVERT  = 'EVENT_OUVERT'
    TYPE_EVENT_FERME   = 'EVENT_FERME'
    TYPE_CHOICES = [
        (TYPE_AGENT_AJOUTE, 'Nouvel agent ajouté'),
        (TYPE_COMPTE_CREE,  'Compte créé'),
        (TYPE_EVENT_OUVERT, 'Événement ouvert'),
        (TYPE_EVENT_FERME,  'Événement fermé'),
    ]

    destinataire = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                     related_name='notifications')
    type_notif   = models.CharField(max_length=30, choices=TYPE_CHOICES)
    titre        = models.CharField(max_length=200)
    message      = models.TextField()
    lue          = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} → {self.destinataire}"

    @classmethod
    def envoyer(cls, destinataire, type_notif, titre, message):
        return cls.objects.create(
            destinataire=destinataire,
            type_notif=type_notif,
            titre=titre,
            message=message,
        )


class ActionLog(models.Model):
    ACTION_LOGIN          = 'LOGIN'
    ACTION_LOGOUT         = 'LOGOUT'
    ACTION_SAISIE         = 'SAISIE'
    ACTION_EVENT_CREATE   = 'EVENT_CREATE'
    ACTION_EVENT_EDIT     = 'EVENT_EDIT'
    ACTION_EXPORT         = 'EXPORT'
    ACTION_ACCOUNT_CREATE = 'ACCOUNT_CREATE'
    ACTION_ACCOUNT_TOGGLE = 'ACCOUNT_TOGGLE'
    ACTION_AGENT_ADD      = 'AGENT_ADD'

    ACTION_CHOICES = [
        (ACTION_LOGIN,          'Connexion'),
        (ACTION_LOGOUT,         'Déconnexion'),
        (ACTION_SAISIE,         'Saisie demande'),
        (ACTION_EVENT_CREATE,   'Création événement'),
        (ACTION_EVENT_EDIT,     'Modification événement'),
        (ACTION_EXPORT,         'Export données'),
        (ACTION_ACCOUNT_CREATE, 'Création compte'),
        (ACTION_ACCOUNT_TOGGLE, 'Activation/Désactivation'),
        (ACTION_AGENT_ADD,      'Ajout agent'),
    ]

    utilisateur = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='actions')
    type_action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    date_heure  = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-date_heure']

    def __str__(self):
        return f"[{self.date_heure:%d/%m/%Y %H:%M}] {self.utilisateur} – {self.get_type_action_display()}"

    @classmethod
    def log(cls, request, type_action, description=""):
        user = request.user if request.user.is_authenticated else None
        ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
              or request.META.get('REMOTE_ADDR'))
        cls.objects.create(utilisateur=user, type_action=type_action,
                           description=description, ip_address=ip or None)