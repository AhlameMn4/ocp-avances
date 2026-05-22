"""Vues supplémentaires : saisie rapide AJAX + export PDF.
À importer dans demandes/views.py ou inclure dans demandes/urls.py.
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from accounts.decorators import gestionnaire_required, admin_required
from accounts.models import ActionLog
from events.models import Event
from agents.models import Agent
from .models import Demande


def _statut(event):
    return 'INCLUS' if event.type_avance == Event.TYPE_PREAMENAGEMENT else 'EXCLUS'


@gestionnaire_required
def saisie_rapide(request, event_pk):
    """Page de saisie rapide avec compteurs live."""
    from django.db.models import Count, Q
    ev = get_object_or_404(Event, pk=event_pk)

    if not ev.est_actif:
        from django.contrib import messages
        messages.info(request, "Cet événement est clôturé.")
        return __import__('django.shortcuts', fromlist=['redirect']).redirect('events:gestionnaire_events')

    mes_demandes = Demande.objects.filter(
        event=ev, gestionnaire=request.user
    ).select_related('agent').order_by('-date_saisie')

    lbl, color, desc = ev.logique
    return render(request, 'demandes/saisie_rapide.html', {
        'ev':          ev,
        'mes_demandes':mes_demandes,
        'total':       mes_demandes.count(),
        'nb_inclus':   mes_demandes.filter(statut='INCLUS').count(),
        'nb_exclus':   mes_demandes.filter(statut='EXCLUS').count(),
        'logique_label': lbl,
        'logique_color': color,
        'logique_desc':  desc,
    })


@require_POST
@gestionnaire_required
def ajax_saisie(request, event_pk):
    """Endpoint AJAX pour la saisie rapide."""
    ev = get_object_or_404(Event, pk=event_pk)

    if not ev.est_actif:
        return JsonResponse({'ok': False, 'error': 'Événement clôturé.'})

    try:
        body      = json.loads(request.body)
        matricule = body.get('matricule', '').strip().upper()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'ok': False, 'error': 'Requête invalide.'})

    try:
        agent = Agent.objects.get(matricule=matricule)
    except Agent.DoesNotExist:
        return JsonResponse({'ok': False, 'error': f'Matricule {matricule} introuvable.'})

    # Vérification doublon
    if Demande.objects.filter(agent=agent, event=ev).exists():
        return JsonResponse({'ok': False, 'doublon': True,
                             'error': f'{agent.nom_complet} déjà saisi pour cet événement.'})

    # Enregistrement
    statut  = _statut(ev)
    demande = Demande.objects.create(
        agent=agent, event=ev,
        gestionnaire=request.user, statut=statut
    )
    ActionLog.log(request, ActionLog.ACTION_SAISIE,
                  f"{agent.nom_complet} – {ev} [{statut}]")

    # Totaux mis à jour
    qs = Demande.objects.filter(event=ev, gestionnaire=request.user)
    return JsonResponse({
        'ok': True,
        'demande': {
            'matricule':  agent.matricule,
            'nom_complet':agent.nom_complet,
            'service':    agent.service,
            'statut':     demande.get_statut_display(),
            'heure':      demande.date_saisie.strftime('%H:%M:%S'),
        },
        'totaux': {
            'total':  qs.count(),
            'inclus': qs.filter(statut='INCLUS').count(),
            'exclus': qs.filter(statut='EXCLUS').count(),
        }
    })


# ── Export PDF ──────────────────────────────────────────────────────────────

@admin_required
def export_pdf(request):
    """Export PDF officiel d'un événement, prêt pour archivage RH."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                     TableStyle, HRFlowable, Image)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    import io

    event_id = request.GET.get('event')
    qs = Demande.objects.select_related('agent', 'event', 'gestionnaire').all()

    if event_id:
        ev = get_object_or_404(Event, pk=event_id)
        qs = qs.filter(event=ev)
    else:
        ev = None

    service     = request.GET.get('service', '')
    statut      = request.GET.get('statut', '')
    type_avance = request.GET.get('type_avance', '')
    if service:     qs = qs.filter(agent__service__icontains=service)
    if statut:      qs = qs.filter(statut=statut)
    if type_avance: qs = qs.filter(event__type_avance=type_avance)

    ActionLog.log(request, ActionLog.ACTION_EXPORT,
                  f"Export PDF – {qs.count()} demandes")

    # ── Couleurs OCP ──
    OCP_BLUE   = colors.HexColor('#005EB8')
    OCP_DARK   = colors.HexColor('#002f6e')
    OCP_LIGHT  = colors.HexColor('#e8f0fa')
    OCP_GREEN  = colors.HexColor('#1a7b4b')
    OCP_RED    = colors.HexColor('#c0392b')
    GRAY_TEXT  = colors.HexColor('#6b7280')
    DARK_TEXT  = colors.HexColor('#1a2540')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=f"Avances Sociales OCP – Export",
    )

    styles = getSampleStyleSheet()
    story  = []

    # En-tête
    header_data = [[
        Paragraph('<b><font size="18" color="#005EB8">OCP</font></b> &nbsp;'
                  '<font size="11" color="#6b7280">Group</font>', styles['Normal']),
        Paragraph(
            f'<font size="9" color="#9ca3af">Généré le '
            f'{timezone.now().strftime("%d/%m/%Y à %H:%M")}</font>',
            ParagraphStyle('r', alignment=TA_RIGHT, parent=styles['Normal'])
        )
    ]]
    t = Table(header_data, colWidths=[9*cm, 8*cm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t)
    story.append(HRFlowable(width='100%', thickness=2, color=OCP_BLUE, spaceAfter=16))

    # Titre principal
    titre_txt = f"Avances Sociales – {ev}" if ev else "Export Avances Sociales"
    story.append(Paragraph(
        f'<b><font size="16" color="#1a2540">{titre_txt}</font></b>',
        ParagraphStyle('ct', alignment=TA_CENTER, parent=styles['Normal'], spaceAfter=4)
    ))
    story.append(Paragraph(
        '<font size="10" color="#6b7280">Direction des Ressources Humaines – OCP Group</font>',
        ParagraphStyle('ct2', alignment=TA_CENTER, parent=styles['Normal'], spaceAfter=20)
    ))

    # Résumé statistique
    total  = qs.count()
    inclus = qs.filter(statut='INCLUS').count()
    exclus = qs.filter(statut='EXCLUS').count()

    stats_data = [
        ['Total demandes', 'Agents inclus', 'Agents exclus',
         'Période' if ev else 'Type'],
        [
            Paragraph(f'<b><font size="18" color="#005EB8">{total}</font></b>', styles['Normal']),
            Paragraph(f'<b><font size="18" color="#1a7b4b">{inclus}</font></b>', styles['Normal']),
            Paragraph(f'<b><font size="18" color="#c0392b">{exclus}</font></b>', styles['Normal']),
            Paragraph(
                f'<font size="9" color="#374151">'
                f'{ev.date_debut.strftime("%d/%m/%Y") + " → " + ev.date_fin.strftime("%d/%m/%Y") if ev else "Tous types"}'
                f'</font>', styles['Normal']
            ),
        ]
    ]
    ts = Table(stats_data, colWidths=[4.25*cm]*4)
    ts.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), OCP_LIGHT),
        ('TEXTCOLOR',     (0,0), (-1,0), GRAY_TEXT),
        ('FONTSIZE',      (0,0), (-1,0), 8),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica'),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#e5eaf3')),
        ('ROUNDEDCORNERS',(0,0), (-1,-1), [6,6,6,6]),
    ]))
    story.append(ts)
    story.append(Spacer(1, 20))

    # Table principale
    col_headers = ['Matricule','Nom','Prénom','Service','Statut','Gestionnaire','Date saisie']
    col_widths  = [2.4*cm, 3.2*cm, 3*cm, 4*cm, 1.8*cm, 3.2*cm, 2.7*cm]

    def hcell(txt):
        return Paragraph(f'<b><font size="8" color="white">{txt}</font></b>', styles['Normal'])

    def dcell(txt, color='#1a2540', size=8, bold=False):
        b = 'b' if bold else 'font'
        return Paragraph(f'<{b}><font size="{size}" color="{color}">{txt}</font></{b}>', styles['Normal'])

    rows = [[hcell(h) for h in col_headers]]
    for i, d in enumerate(qs):
        sc = '#155724' if d.statut == 'INCLUS' else '#721c24'
        sb = '#d4edda' if d.statut == 'INCLUS' else '#f8d7da'
        rows.append([
            dcell(d.agent.matricule, '#005EB8', bold=True),
            dcell(d.agent.nom),
            dcell(d.agent.prenom),
            dcell(d.agent.service, '#374151', size=7),
            Paragraph(
                f'<b><font size="8" color="{sc}">{d.get_statut_display()}</font></b>',
                styles['Normal']
            ),
            dcell(d.gestionnaire.get_full_name(), '#374151', size=7),
            dcell(d.date_saisie.strftime('%d/%m/%Y'), '#6b7280', size=7),
        ])

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), OCP_BLUE),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, OCP_LIGHT]),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#e5eaf3')),
        ('FONTNAME',      (0,0), (-1,-1), 'Helvetica'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 20))

    # Pied de page
    story.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#e5eaf3'), spaceAfter=10))
    story.append(Paragraph(
        f'<font size="8" color="#9ca3af">'
        f'Document confidentiel – OCP Group · Direction RH · '
        f'Exporté par {request.user.get_full_name()} le '
        f'{timezone.now().strftime("%d/%m/%Y à %H:%M")}'
        f'</font>',
        ParagraphStyle('foot', alignment=TA_CENTER, parent=styles['Normal'])
    ))

    doc.build(story)
    buffer.seek(0)

    fname = f"avances_ocp_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    return response