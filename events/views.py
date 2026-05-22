from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import admin_required, gestionnaire_required
from accounts.models import ActionLog, Notification, CustomUser
from .models import Event


def _auto_close():
    Event.fermer_expires()


@admin_required
def liste_events(request):
    _auto_close()
    events = Event.objects.select_related('cree_par').all()
    actifs = [e for e in events if e.est_actif]
    fermes = [e for e in events if not e.est_actif]
    return render(request, 'events/liste.html', {
        'events': events, 'actifs': actifs, 'fermes': fermes
    })


@admin_required
def creer_event(request):
    error = None
    if request.method == 'POST':
        type_avance = request.POST.get('type_avance')
        annee = request.POST.get('annee')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        description = request.POST.get('description', '')

        from datetime import date
        try:
            dd = date.fromisoformat(date_debut)
            df = date.fromisoformat(date_fin)
            if df <= dd:
                error = "La date de fin doit être après la date de début."
            else:
                ev = Event.objects.create(
                    type_avance=type_avance, annee=annee,
                    date_debut=dd, date_fin=df,
                    description=description, cree_par=request.user,
                    statut=Event.STATUT_ACTIF,
                )
                ActionLog.log(request, ActionLog.ACTION_EVENT_CREATE, f"Événement créé : {ev}")
                # Notifier tous les gestionnaires actifs
                gestionnaires = CustomUser.objects.filter(
                    role=CustomUser.ROLE_GESTIONNAIRE, actif=True)
                for g in gestionnaires:
                    Notification.envoyer(
                        destinataire=g,
                        type_notif=Notification.TYPE_EVENT_OUVERT,
                        titre=f"Nouvelle campagne ouverte – {ev}",
                        message=(
                            f"L'administrateur RH a ouvert la campagne "
                            f"« {ev.get_type_avance_display()} {ev.annee} ». "
                            f"Période : {ev.date_debut.strftime('%d/%m/%Y')} → "
                            f"{ev.date_fin.strftime('%d/%m/%Y')}. "
                            f"Vous pouvez commencer la saisie."
                        ),
                    )
                messages.success(request, f"Événement « {ev} » créé avec succès.")
                return redirect('events:liste')
        except ValueError:
            error = "Dates invalides."

    return render(request, 'events/form.html', {
        'titre': 'Créer un événement', 'error': error,
        'type_choices': Event.TYPE_CHOICES,
    })


@admin_required
def modifier_event(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    error = None
    if ev.statut == Event.STATUT_FERME:
        messages.warning(request, "Impossible de modifier un événement clôturé.")
        return redirect('events:liste')

    if request.method == 'POST':
        from datetime import date
        try:
            ev.type_avance  = request.POST.get('type_avance', ev.type_avance)
            ev.annee        = request.POST.get('annee', ev.annee)
            ev.date_debut   = date.fromisoformat(request.POST.get('date_debut'))
            ev.date_fin     = date.fromisoformat(request.POST.get('date_fin'))
            ev.description  = request.POST.get('description', '')
            if ev.date_fin <= ev.date_debut:
                error = "La date de fin doit être après la date de début."
            else:
                ev.save()
                ActionLog.log(request, ActionLog.ACTION_EVENT_EDIT, f"Événement modifié : {ev}")
                messages.success(request, "Événement mis à jour.")
                return redirect('events:liste')
        except ValueError:
            error = "Dates invalides."

    return render(request, 'events/form.html', {
        'titre': "Modifier l'événement", 'ev': ev, 'error': error,
        'type_choices': Event.TYPE_CHOICES,
    })


@admin_required
def supprimer_event(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if ev.demandes.exists():
        messages.error(request, "Impossible : cet événement contient des demandes. Il sera conservé dans l'historique.")
        return redirect('events:liste')
    if request.method == 'POST':
        nom = str(ev)
        ev.delete()
        messages.success(request, f"Événement « {nom} » supprimé.")
        return redirect('events:liste')
    return render(request, 'events/confirmer_suppression.html', {'ev': ev})


@admin_required
def detail_event(request, pk):
    _auto_close()
    ev = get_object_or_404(Event, pk=pk)
    from demandes.models import Demande
    from django.db.models import Count
    demandes = Demande.objects.filter(event=ev).select_related('agent', 'gestionnaire')
    stats_service = demandes.values('agent__service').annotate(total=Count('id')).order_by('-total')
    return render(request, 'events/detail.html', {
        'ev': ev, 'demandes': demandes,
        'stats_service': stats_service,
        'total': demandes.count(),
        'inclus': demandes.filter(statut='INCLUS').count(),
        'exclus': demandes.filter(statut='EXCLUS').count(),
    })


@gestionnaire_required
def events_gestionnaire(request):
    _auto_close()
    today = timezone.now().date()
    events_actifs = Event.objects.filter(
        statut=Event.STATUT_ACTIF, date_debut__lte=today, date_fin__gte=today
    )
    events_fermes = Event.objects.filter(statut=Event.STATUT_FERME).order_by('-date_fin')[:8]
    return render(request, 'events/gestionnaire_events.html', {
        'events_actifs': events_actifs, 'events_fermes': events_fermes,
    })