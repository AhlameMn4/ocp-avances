from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('lookup/',                           views.lookup_agent,     name='lookup'),
    path('mes-agents/',                       views.mes_agents,       name='mes_agents'),
    path('admin/',                            views.admin_agents,     name='admin_agents'),
    path('admin/<str:matricule>/modifier/',   views.modifier_agent,   name='modifier'),
    path('admin/<str:matricule>/supprimer/',  views.supprimer_agent,  name='supprimer'),
    path('admin/<str:matricule>/historique/', views.historique_agent, name='historique'),
]