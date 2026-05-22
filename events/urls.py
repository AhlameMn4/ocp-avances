from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('',                      views.liste_events,        name='liste'),
    path('creer/',                views.creer_event,         name='creer'),
    path('<int:pk>/modifier/',    views.modifier_event,      name='modifier'),
    path('<int:pk>/supprimer/',   views.supprimer_event,     name='supprimer'),
    path('<int:pk>/detail/',      views.detail_event,        name='detail'),
    path('mes-events/',           views.events_gestionnaire, name='gestionnaire_events'),
]