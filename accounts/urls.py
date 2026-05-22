from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',                            views.login_view,              name='login'),
    path('logout/',                           views.logout_view,             name='logout'),
    path('change-password/',                  views.change_password_view,    name='change_password'),
    path('profil/',                           views.mon_profil,              name='mon_profil'),
    path('profil/modifier/',                  views.modifier_profil,         name='modifier_profil'),
    # Notifications
    path('notifications/',                    views.mes_notifications,       name='mes_notifications'),
    path('notifications/<int:pk>/lue/',       views.marquer_notif_lue,      name='notif_lue'),
    path('notifications/toutes-lues/',        views.marquer_toutes_lues,    name='notifs_lues'),
    # Gestionnaires
    path('gestionnaires/',                    views.liste_gestionnaires,     name='liste_gestionnaires'),
    path('gestionnaires/creer/',              views.creer_gestionnaire,      name='creer_gestionnaire'),
    path('gestionnaires/<int:pk>/modifier/',  views.modifier_gestionnaire,   name='modifier_gestionnaire'),
    path('gestionnaires/<int:pk>/toggle/',    views.toggle_gestionnaire,     name='toggle_gestionnaire'),
    path('gestionnaires/<int:pk>/supprimer/', views.supprimer_gestionnaire,  name='supprimer_gestionnaire'),
    path('gestionnaires/<int:pk>/profil/',    views.profil_gestionnaire,     name='profil_gestionnaire'),
]