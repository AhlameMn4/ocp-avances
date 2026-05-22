from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'home.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('agents/',   include('agents.urls')),
    path('events/',   include('events.urls')),
    path('demandes/', include('demandes.urls')),
    path('dashboard/',include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)