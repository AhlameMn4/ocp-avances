from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from .models import CustomUser
import secrets
import string


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email / Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Votre identifiant',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••••••',
        })
    )


class CreateGestionnaireForm(forms.ModelForm):
    """Formulaire de création d'un compte gestionnaire par l'admin."""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'service']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'service':    forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name':  'Nom',
            'username':   "Nom d'utilisateur",
            'email':      'Email professionnel',
            'service':    'Service',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.ROLE_GESTIONNAIRE
        user.actif = True
        user.must_change_password = True
        # Générer un mot de passe aléatoire sécurisé
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        user._plain_password = password  # Pour l'envoyer par email
        user.set_password(password)
        if commit:
            user.save()
        return user


class EditGestionnaireForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'service', 'actif']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'service':    forms.TextInput(attrs={'class': 'form-control'}),
            'actif':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'Prénom',
            'last_name':  'Nom',
            'email':      'Email',
            'service':    'Service',
            'actif':      'Compte actif',
        }


class ChangePasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    new_password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )