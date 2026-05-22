from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',               views.index,               name='index'),
    path('admin/',         views.admin_dashboard,      name='admin'),
    path('gestionnaire/',  views.gestionnaire_dashboard,name='gestionnaire'),
    path('statistiques/',  views.statistiques,         name='statistiques'),
]