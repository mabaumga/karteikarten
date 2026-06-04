"""URL configuration for Karteikarten project."""
from django.contrib import admin
from django.urls import path, include

from karteikarten.health_views import health

urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('', include('karteikarten.urls')),
]
