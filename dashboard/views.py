from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from events.models import Event
from demandes.models import Demande
from agents.models import Agent
from accounts.models import CustomUser, ActionLog, Notification


@login_required
def index(request):
    if request.user.is_admin_rh:
        return redirect('dashboard:admin')
    return redirect('dashboard:gestionnaire')


@login_required
def admin_dashboard(request):
    if not request.user.is_admin_rh:
        return redirect('dashboard:gestionnaire')

    Event.fermer_expires()
    today = timezone.now().date()

    total_demandes     = Demande.objects.count()
    total_inclus       = Demande.objects.filter(statut='INCLUS').count()
    total_exclus       = Demande.objects.filter(statut='EXCLUS').count()
    total_agents       = Agent.objects.count()
    total_gestionnaires = CustomUser.objects.filter(
        role=CustomUser.ROLE_GESTIONNAIRE, actif=True).count()

    events_actifs = Event.objects.filter(
        statut=Event.STATUT_ACTIF, date_debut__lte=today, date_fin__gte=today)
    nb_events_actifs = events_actifs.count()
    nb_events_fermes = Event.objects.filter(statut=Event.STATUT_FERME).count()

    alertes = events_actifs.filter(
        date_fin__lte=today + timezone.timedelta(days=2))

    stats_service = (Demande.objects
                     .values('agent__service')
                     .annotate(total=Count('id'))
                     .order_by('-total')[:8])

    stats_type = (Demande.objects
                  .values('event__type_avance')
                  .annotate(total=Count('id')))

    # Stats inclus/exclus par événement (pour graphique empilé)
    stats_event = (Event.objects
                   .annotate(
                       nb_inclus=Count('demandes', filter=Q(demandes__statut='INCLUS')),
                       nb_exclus=Count('demandes', filter=Q(demandes__statut='EXCLUS')),
                   )
                   .filter(Q(nb_inclus__gt=0) | Q(nb_exclus__gt=0))
                   .order_by('-date_debut')[:6])

    logs = ActionLog.objects.select_related('utilisateur').all()[:10]

    return render(request, 'dashboard/admin.html', {
        'total_demandes':     total_demandes,
        'total_inclus':       total_inclus,
        'total_exclus':       total_exclus,
        'total_agents':       total_agents,
        'total_gestionnaires':total_gestionnaires,
        'nb_events_actifs':   nb_events_actifs,
        'nb_events_fermes':   nb_events_fermes,
        'events_actifs':      events_actifs,
        'alertes':            alertes,
        'stats_service':      list(stats_service),
        'stats_type':         list(stats_type),
        'stats_event':        list(stats_event),
        'logs':               logs,
    })


@login_required
def gestionnaire_dashboard(request):
    if not request.user.is_gestionnaire:
        return redirect('dashboard:admin')

    Event.fermer_expires()
    today = timezone.now().date()
    user  = request.user

    events_actifs = Event.objects.filter(
        statut=Event.STATUT_ACTIF, date_debut__lte=today, date_fin__gte=today)

    mes_demandes = Demande.objects.filter(
        gestionnaire=user).select_related('agent', 'event')

    agents_service = Agent.objects.filter(service=user.service)
    nb_agents = agents_service.count()

    stats_par_event = (
        mes_demandes
        .values('event__type_avance', 'event__annee', 'event__id')
        .annotate(nb=Count('id'))
        .order_by('-event__date_debut')[:6]
    )

    notifs_non_lues = Notification.objects.filter(
        destinataire=user, lue=False).count()

    return render(request, 'dashboard/gestionnaire.html', {
        'events_actifs':   events_actifs,
        'nb_events_actifs':events_actifs.count(),
        'mes_demandes':    mes_demandes[:8],
        'nb_agents':       nb_agents,
        'stats': {
            'total':  mes_demandes.count(),
            'inclus': mes_demandes.filter(statut='INCLUS').count(),
            'exclus': mes_demandes.filter(statut='EXCLUS').count(),
        },
        'stats_par_event':  list(stats_par_event),
        'notifs_non_lues':  notifs_non_lues,
    })

@login_required
def statistiques(request):
    """Page statistiques dédiée – Admin uniquement."""
    if not request.user.is_admin_rh:
        return redirect('dashboard:gestionnaire')

    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import date, timedelta
    from events.models import Event
    from demandes.models import Demande
    from agents.models import Agent
    from accounts.models import CustomUser

    total_demandes = Demande.objects.count()
    total_inclus   = Demande.objects.filter(statut='INCLUS').count()
    total_exclus   = Demande.objects.filter(statut='EXCLUS').count()
    total_agents   = Agent.objects.count()
    nb_events      = Event.objects.count()

    # Stats par service
    stats_service = (
        Demande.objects.values('agent__service')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )

    # Stats par type
    stats_type = (
        Demande.objects.values('event__type_avance')
        .annotate(total=Count('id'))
    )

    # Évolution mensuelle (12 derniers mois)
    today = date.today()
    evolution = []
    for i in range(11, -1, -1):
        mois_date = (today.replace(day=1) - timedelta(days=i * 30))
        m = mois_date.month
        y = mois_date.year
        total_m = Demande.objects.filter(
            date_saisie__month=m, date_saisie__year=y
        ).count()
        evolution.append({
            'mois': f"{mois_date.strftime('%b')} {y}",
            'total': total_m,
        })

    # Comparaison inter-éditions (tous les événements avec demandes)
    events_avec = (
        Event.objects.annotate(
            nb_inclus=Count('demandes', filter=Q(demandes__statut='INCLUS')),
            nb_exclus=Count('demandes', filter=Q(demandes__statut='EXCLUS')),
        ).filter(Q(nb_inclus__gt=0) | Q(nb_exclus__gt=0))
        .order_by('type_avance', 'annee')
    )
    comparaison = [
        {
            'label':  f"{ev.get_type_avance_display()} {ev.annee}",
            'inclus': ev.nb_inclus,
            'exclus': ev.nb_exclus,
        }
        for ev in events_avec
    ]

    # Stats gestionnaires
    from django.db.models import Count, Q
    stats_gestionnaires = (
        Demande.objects
        .values('gestionnaire__first_name', 'gestionnaire__last_name',
                'gestionnaire__service')
        .annotate(
            total=Count('id'),
            nb_inclus=Count('id', filter=Q(statut='INCLUS')),
            nb_exclus=Count('id', filter=Q(statut='EXCLUS')),
        )
        .order_by('-total')
    )
    max_saisies = stats_gestionnaires[0]['total'] if stats_gestionnaires else 1

    return render(request, 'dashboard/statistiques.html', {
        'total_demandes':     total_demandes,
        'total_inclus':       total_inclus,
        'total_exclus':       total_exclus,
        'total_agents':       total_agents,
        'nb_events':          nb_events,
        'stats_service':      list(stats_service),
        'stats_type':         list(stats_type),
        'evolution_mensuelle':evolution,
        'comparaison':        comparaison,
        'stats_gestionnaires':list(stats_gestionnaires),
        'max_saisies':        max_saisies,
    })