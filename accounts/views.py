import io, secrets, string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import JsonResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .models import CustomUser, ActionLog, Notification
from .decorators import admin_required, gestionnaire_required


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    error = None
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.actif:
                error = "Votre compte est désactivé. Contactez l'administrateur RH."
            else:
                login(request, user)
                ActionLog.log(request, ActionLog.ACTION_LOGIN,
                              f"Connexion de {user.get_full_name()}")
                if user.must_change_password:
                    return redirect('accounts:change_password')
                return redirect('dashboard:index')
        else:
            error = "Identifiants incorrects. Veuillez réessayer."
    return render(request, 'accounts/login.html', {'error': error})


@login_required
def logout_view(request):
    ActionLog.log(request, ActionLog.ACTION_LOGOUT,
                  f"Déconnexion de {request.user.get_full_name()}")
    logout(request)
    return redirect('home')   # ← page d'accueil après déconnexion


@login_required
def change_password_view(request):
    error = None
    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')
        if len(p1) < 8:
            error = "Le mot de passe doit contenir au moins 8 caractères."
        elif p1 != p2:
            error = "Les mots de passe ne correspondent pas."
        else:
            request.user.set_password(p1)
            request.user.must_change_password = False
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect('dashboard:index')
    return render(request, 'accounts/change_password.html', {'error': error})


# ── Profil ────────────────────────────────────────────────────────────────────

@login_required
def mon_profil(request):
    """Affiche uniquement les informations personnelles — pas de formulaire ici."""
    return render(request, 'accounts/profil.html', {'user': request.user})




@login_required
def modifier_profil(request):
    """Page indépendante de modification du profil."""
    user = request.user
    error = None
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        telephone  = request.POST.get('telephone', '').strip()
        if not first_name or not last_name:
            error = "Le prénom et le nom sont obligatoires."
        else:
            user.first_name = first_name
            user.last_name  = last_name
            user.telephone  = telephone
            user.save()
            messages.success(request, "Vos informations ont été mises à jour.")
            return redirect('accounts:mon_profil')
    return render(request, 'accounts/modifier_profil.html', {'user': user, 'error': error})

@login_required
def mes_notifications(request):
    """Page dédiée à toutes les notifications de l'utilisateur."""
    notifs = Notification.objects.filter(destinataire=request.user).order_by('-date_creation')
    non_lues = notifs.filter(lue=False).count()

    # Marquer comme lue si on clique depuis la page
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marquer_toutes':
            notifs.update(lue=True)
            messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        elif action == 'supprimer_lues':
            notifs.filter(lue=True).delete()
            messages.success(request, "Notifications lues supprimées.")
        return redirect('accounts:mes_notifications')

    return render(request, 'accounts/notifications.html', {
        'notifs':    notifs,
        'non_lues':  non_lues,
        'total':     notifs.count(),
    })


@login_required
def marquer_notif_lue(request, pk):
    """Marque une notification comme lue via AJAX ou redirect."""
    notif = get_object_or_404(Notification, pk=pk, destinataire=request.user)
    notif.lue = True
    notif.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect(request.META.get('HTTP_REFERER', 'accounts:mes_notifications'))


@login_required
def marquer_toutes_lues(request):
    """Marque toutes les notifications non lues comme lues."""
    count = Notification.objects.filter(destinataire=request.user, lue=False).update(lue=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'count': count})
    messages.success(request, f"{count} notification(s) marquée(s) comme lues.")
    return redirect(request.META.get('HTTP_REFERER', 'accounts:mes_notifications'))


# ── Gestionnaires (admin) ─────────────────────────────────────────────────────

@admin_required
def liste_gestionnaires(request):
    from agents.models import Agent
    from demandes.models import Demande
    gestionnaires = CustomUser.objects.filter(
        role=CustomUser.ROLE_GESTIONNAIRE
    ).order_by('last_name', 'first_name')
    data = []
    for g in gestionnaires:
        data.append({
            'user': g,
            'nb_agents': Agent.objects.filter(service=g.service).count(),
            'nb_demandes': Demande.objects.filter(gestionnaire=g).count(),
        })
    return render(request, 'accounts/liste_gestionnaires.html', {'data': data})


def _generer_pdf_compte(user, plain_password):
    """Génère un PDF avec les identifiants du gestionnaire."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    ocp_blue = colors.HexColor('#005EB8')
    ocp_dark = colors.HexColor('#003f8a')

    title_style = ParagraphStyle('title', parent=styles['Normal'],
        fontSize=20, fontName='Helvetica-Bold', textColor=ocp_blue,
        alignment=TA_CENTER, spaceAfter=6)
    sub_style = ParagraphStyle('sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER, spaceAfter=4)
    label_style = ParagraphStyle('label', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#374151'))
    value_style = ParagraphStyle('value', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#1a2540'))
    warn_style = ParagraphStyle('warn', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#c0392b'), alignment=TA_CENTER)

    story = []
    story.append(Paragraph("OCP Group", title_style))
    story.append(Paragraph("Direction des Ressources Humaines", sub_style))
    story.append(Paragraph("Plateforme de Gestion des Avances Sociales", sub_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ocp_blue))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Identifiants de connexion – Compte Gestionnaire", ParagraphStyle(
        'ht', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold',
        textColor=ocp_dark, alignment=TA_CENTER, spaceAfter=16)))

    rows = [
        ['Nom complet',  user.get_full_name()],
        ["Nom d'utilisateur", user.username],
        ['Email',        user.email],
        ['Service',      user.service or '—'],
        ['Mot de passe temporaire', plain_password],
        ['URL de connexion', 'http://localhost:8000/accounts/login/'],
    ]
    table = Table(rows, colWidths=[5.5*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, -1), colors.HexColor('#e8f0fa')),
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',   (0, 0), (0, -1), ocp_blue),
        ('TEXTCOLOR',   (1, 0), (1, -1), colors.HexColor('#1a2540')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING',  (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('FONTNAME',    (1, 4), (1, 4), 'Helvetica-Bold'),
        ('TEXTCOLOR',   (1, 4), (1, 4), colors.HexColor('#005EB8')),
        ('FONTSIZE',    (1, 4), (1, 4), 12),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "⚠️  Ce mot de passe est temporaire. Vous devrez le modifier à votre première connexion.",
        warn_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Ce document est confidentiel. Ne le partagez pas.", warn_style))
    story.append(Spacer(1, 0.6*cm))
    from datetime import datetime
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} – OCP Group RH",
        ParagraphStyle('foot', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#9ca3af'), alignment=TA_CENTER)))
    doc.build(story)
    buffer.seek(0)
    return buffer


def _gen_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(12))


@admin_required
def creer_gestionnaire(request):
    """
    Création gestionnaire CONDITIONNELLE :
    Le compte n'est créé QUE si l'email est valide ET que l'envoi du PDF réussit.
    Aucun compte créé si l'email échoue.
    """
    import re, socket
    error = None

    if request.method == 'POST':
        prenom    = request.POST.get('first_name', '').strip()
        nom       = request.POST.get('last_name',  '').strip()
        username  = request.POST.get('username',   '').strip()
        email     = request.POST.get('email',      '').strip()
        service   = request.POST.get('service',    '').strip()
        telephone = request.POST.get('telephone',  '').strip()

        # 1. Validation champs obligatoires
        if not all([prenom, nom, username, email, service]):
            error = "Tous les champs obligatoires (*) doivent être remplis."

        elif not re.match(r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$', email):
            error = "L'adresse email est invalide (format incorrect)."

        elif CustomUser.objects.filter(username=username).exists():
            error = f"Le nom d'utilisateur '{username}' est déjà utilisé."

        elif CustomUser.objects.filter(email=email).exists():
            error = f"Un compte existe déjà avec l'email '{email}'."

        else:
            # 2. Vérification DNS du domaine
            try:
                domain = email.split('@')[1]
                socket.getaddrinfo(domain, None)
            except (IndexError, socket.gaierror):
                error = (
                    f"Le domaine '{email.split('@')[-1] if '@' in email else email}' "
                    f"est introuvable. Vérifiez l'adresse email — aucun compte n'a été créé."
                )

        if not error:
            # 3. Générer mot de passe + PDF (avant de créer le compte)
            plain_password = _gen_password()
            temp_user = CustomUser(
                username=username, email=email,
                first_name=prenom, last_name=nom,
                service=service, telephone=telephone,
            )
            pdf_buffer = _generer_pdf_compte(temp_user, plain_password)

            # 4. Tenter l'envoi email (bloquant — si ça échoue, pas de compte)
            # Si EMAIL_BACKEND = console, on sauvegarde le PDF localement pour dev
            from django.conf import settings as dj_settings
            is_console = 'console' in dj_settings.EMAIL_BACKEND

            if is_console:
                # Mode développement : sauvegarder le PDF localement
                import os
                pdf_path = os.path.join(dj_settings.MEDIA_ROOT, 'pdf_comptes')
                os.makedirs(pdf_path, exist_ok=True)
                pdf_file = os.path.join(pdf_path, f"identifiants_{username}.pdf")
                with open(pdf_file, 'wb') as f:
                    f.write(pdf_buffer.read())
                # En mode console, on considère l'email comme "envoyé"
                import logging
                logging.getLogger(__name__).info(
                    f"[DEV] PDF sauvegardé : {pdf_file} | MDP: {plain_password}")
            else:
                try:
                    from django.core.mail import EmailMessage as DjEmailMessage
                    pdf_buffer.seek(0)
                    mail = DjEmailMessage(
                        subject="[OCP Avances Sociales] Vos identifiants de connexion",
                        body=(
                            f"Bonjour {prenom} {nom},\n\n"
                            f"Un compte Gestionnaire a été créé pour vous sur la "
                            f"plateforme OCP Avances Sociales.\n\n"
                            f"Veuillez trouver ci-joint votre document confidentiel "
                            f"contenant vos identifiants et votre mot de passe temporaire.\n\n"
                            f"Connectez-vous ici : http://localhost:8000/accounts/login/\n"
                            f"Vous devrez changer votre mot de passe à la première connexion.\n\n"
                            f"Cordialement,\nAdministration RH – OCP Group"
                        ),
                        from_email=dj_settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                    )
                    mail.attach(
                        f"identifiants_{username}.pdf",
                        pdf_buffer.read(),
                        'application/pdf'
                    )
                    mail.send(fail_silently=False)
                except Exception as e:
                    error = (
                        f"Impossible d'envoyer l'email à '{email}' : {e}. "
                        f"Vérifiez la configuration SMTP dans settings.py "
                        f"(EMAIL_HOST_USER / EMAIL_HOST_PASSWORD). "
                        f"Aucun compte n'a été créé."
                    )

        if not error:
            # 5. Créer le compte uniquement si email envoyé avec succès
            user = CustomUser.objects.create_user(
                username=username, email=email,
                password=plain_password,
                first_name=prenom, last_name=nom,
                role=CustomUser.ROLE_GESTIONNAIRE,
                service=service, telephone=telephone,
                actif=True, must_change_password=True,
            )
            ActionLog.log(
                request, ActionLog.ACTION_ACCOUNT_CREATE,
                f"Compte créé : {user.get_full_name()} ({email})"
            )
            Notification.envoyer(
                destinataire=request.user,
                type_notif=Notification.TYPE_COMPTE_CREE,
                titre=f"Compte gestionnaire créé – {user.get_full_name()}",
                message=(
                    f"Compte de {user.get_full_name()} ({email}) créé avec succès. "
                    f"PDF envoyé par email."
                ),
            )
            messages.success(
                request,
                f"✓ Compte créé pour {user.get_full_name()}. "
                f"PDF des identifiants envoyé à {email}."
            )
            return redirect('accounts:liste_gestionnaires')

    return render(request, 'accounts/creer_gestionnaire.html', {'error': error})

@admin_required
def modifier_gestionnaire(request, pk):
    gest = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_GESTIONNAIRE)
    error = None
    if request.method == 'POST':
        gest.first_name = request.POST.get('first_name', gest.first_name)
        gest.last_name  = request.POST.get('last_name',  gest.last_name)
        gest.email      = request.POST.get('email',      gest.email)
        gest.service    = request.POST.get('service',    gest.service)
        gest.telephone  = request.POST.get('telephone',  gest.telephone)
        gest.save()
        messages.success(request, f"Compte de {gest.get_full_name()} mis à jour.")
        return redirect('accounts:liste_gestionnaires')
    return render(request, 'accounts/modifier_gestionnaire.html', {'gest': gest, 'error': error})


@admin_required
def toggle_gestionnaire(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_GESTIONNAIRE)
    user.actif = not user.actif
    user.save()
    etat = "activé" if user.actif else "désactivé"
    ActionLog.log(request, ActionLog.ACTION_ACCOUNT_TOGGLE,
                  f"Compte {user.get_full_name()} {etat}")
    messages.success(request, f"Compte de {user.get_full_name()} {etat}.")
    return redirect('accounts:liste_gestionnaires')


@admin_required
def supprimer_gestionnaire(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_GESTIONNAIRE)
    nom = user.get_full_name()
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Compte de {nom} supprimé.")
        return redirect('accounts:liste_gestionnaires')
    return render(request, 'accounts/confirmer_suppression.html', {'gest': user})


@admin_required
def profil_gestionnaire(request, pk):
    gest = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_GESTIONNAIRE)
    from demandes.models import Demande
    from agents.models import Agent
    from django.db.models import Count, Q
    demandes  = Demande.objects.filter(gestionnaire=gest).select_related('agent', 'event')
    agents    = Agent.objects.filter(service=gest.service)
    stats_ev  = demandes.values('event__type_avance', 'event__annee').annotate(nb=Count('id'))
    return render(request, 'accounts/profil_gestionnaire.html', {
        'gest': gest, 'demandes': demandes, 'agents': agents,
        'total': demandes.count(),
        'inclus': demandes.filter(statut='INCLUS').count(),
        'exclus': demandes.filter(statut='EXCLUS').count(),
        'stats_ev': stats_ev,
    })