from django.urls import path
from . import views
from .views_extra import saisie_rapide, ajax_saisie, export_pdf

app_name = 'demandes'

urlpatterns = [
    path('saisie/<int:event_pk>/',              views.saisie,          name='saisie'),
    path('saisie/<int:event_pk>/rapide/',        saisie_rapide,         name='saisie_rapide'),
    path('saisie/<int:event_pk>/ajax/',          ajax_saisie,           name='ajax_saisie'),
    path('saisie/<int:event_pk>/confirmer/',     views.confirmer_saisie,name='confirmer'),
    path('admin/',                               views.liste_admin,     name='liste_admin'),
    path('export/excel/',                        views.export_excel,    name='export_excel'),
    path('export/pdf/',                          export_pdf,            name='export_pdf'),
]