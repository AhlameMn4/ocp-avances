from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from accounts.decorators import admin_required, gestionnaire_required
from accounts.models import CustomUser, Notification, ActionLog
from .models import Agent


@login_required
def lookup_agent(request):
    """AJAX : info agent par matricule."""
    mat = request.GET.get('matricule', '').strip().upper()
    if not mat:
        return JsonResponse({'found': False, 'error': 'Matricule vide'})
    try:
        a = Agent.objects.get(matricule=mat)
        return JsonResponse({
            'found': True, 'matricule': a.matricule,
            'nom': a.nom, 'prenom': a.prenom,
            'service': a.service, 'nom_complet': a.nom_complet,
        })
    except Agent.DoesNotExist:
        return JsonResponse({'found': False, 'error': 'Matricule introuvable dans la base'})


@gestionnaire_required
def mes_agents(request):
    """Gestionnaire : liste lecture-seule de ses agents (même service)."""
    agents = Agent.objects.filter(service=request.user.service)
    # Marquer les notifications d'ajout comme lues
    request.user.notifications.filter(
        type_notif=Notification.TYPE_AGENT_AJOUTE, lue=False
    ).update(lue=True)
    return render(request, 'agents/mes_agents.html', {
        'agents': agents,
        'service': request.user.service,
        'total': agents.count(),
    })


@admin_required
def admin_agents(request):
    """Admin : liste de tous les agents avec filtrage par service."""
    from accounts.models import CustomUser
    service_filter = request.GET.get('service', '')
    agents = Agent.objects.all()
    if service_filter:
        agents = agents.filter(service__icontains=service_filter)
    gestionnaires = CustomUser.objects.filter(role=CustomUser.ROLE_GESTIONNAIRE, actif=True)
    services = Agent.objects.values_list('service', flat=True).distinct().order_by('service')
    return render(request, 'agents/admin_agents.html', {
        'agents': agents, 'services': services,
        'gestionnaires': gestionnaires,
        'service_filter': service_filter,
        'total': agents.count(),
    })


@admin_required
def ajouter_agent(request):
    """Vue désactivée — l'attribution d'agent à un autre service est non autorisée.
    Les agents ont leurs services fixes dans la base OCP."""
    from django.contrib import messages
    messages.warning(request, "L'attribution d'un agent à un autre service n'est pas autorisée dans cette plateforme.")
    return __import__('django.shortcuts', fromlist=['redirect']).redirect('agents:admin_agents')

@admin_required
def modifier_agent(request, matricule):
    agent = get_object_or_404(Agent, matricule=matricule)
    error = None
    if request.method == 'POST':
        agent.nom       = request.POST.get('nom', agent.nom).strip().upper()
        agent.prenom    = request.POST.get('prenom', agent.prenom).strip().title()
        agent.service   = request.POST.get('service', agent.service).strip()
        agent.email     = request.POST.get('email', agent.email).strip()
        agent.telephone = request.POST.get('telephone', agent.telephone).strip()
        agent.poste     = request.POST.get('poste', agent.poste).strip()
        agent.save()
        messages.success(request, f"Agent {agent.nom_complet} mis à jour.")
        return redirect('agents:admin_agents')
    return render(request, 'agents/modifier_agent.html', {'agent': agent, 'error': error})


@admin_required
def supprimer_agent(request, matricule):
    agent = get_object_or_404(Agent, matricule=matricule)
    if request.method == 'POST':
        nom = agent.nom_complet
        agent.delete()
        messages.success(request, f"Agent {nom} supprimé.")
        return redirect('agents:admin_agents')
    return render(request, 'agents/confirmer_suppression.html', {'agent': agent})

@admin_required
def historique_agent(request, matricule):
    """Historique complet de toutes les participations d'un agent."""
    from demandes.models import Demande
    from django.db.models import Count
    agent = get_object_or_404(Agent, matricule=matricule)
    demandes = Demande.objects.filter(agent=agent).select_related(
        'event', 'gestionnaire'
    ).order_by('-date_saisie')
    nb_events_distincts = demandes.values('event').distinct().count()
    return render(request, 'agents/historique_agent.html', {
        'agent':             agent,
        'demandes':          demandes,
        'total_demandes':    demandes.count(),
        'nb_inclus':         demandes.filter(statut='INCLUS').count(),
        'nb_exclus':         demandes.filter(statut='EXCLUS').count(),
        'nb_events_distincts': nb_events_distincts,
    })