"""
services.py – Logique métier des demandes.
Séparé des vues pour respecter la modularité demandée dans le CDC.
"""
from events.models import Event
from agents.models import Agent
from .models import Demande


def determiner_statut(event: Event) -> str:
    """
    Retourne le statut INCLUS ou EXCLUS selon le type d'événement.
    Pré-aménagement → INCLUS
    Aïd / Rentrée   → EXCLUS
    """
    if event.type_avance == Event.TYPE_PREAMENAGEMENT:
        return Demande.STATUT_INCLUS
    return Demande.STATUT_EXCLUS


def verifier_doublon(agent: Agent, event: Event) -> bool:
    """Retourne True si une demande existe déjà pour cet agent et cet événement."""
    return Demande.objects.filter(agent=agent, event=event).exists()


def enregistrer_demande(agent: Agent, event: Event, gestionnaire) -> tuple:
    """
    Enregistre une demande après vérifications.
    Retourne (demande, None) si succès ou (None, message_erreur) si échec.
    """
    # 1. L'événement doit être actif
    if not event.est_actif:
        return None, "Cet événement n'est plus actif. La saisie est clôturée."

    # 2. Vérification doublon
    if verifier_doublon(agent, event):
        return None, f"L'agent {agent.nom_complet} a déjà une demande enregistrée pour cet événement."

    # 3. Détermination automatique du statut
    statut = determiner_statut(event)

    # 4. Création
    demande = Demande.objects.create(
        agent=agent,
        event=event,
        gestionnaire=gestionnaire,
        statut=statut,
    )
    return demande, None