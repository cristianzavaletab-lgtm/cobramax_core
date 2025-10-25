"""
URL configuration for cobramax_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# cobramax_core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('zonas/', include('zonas.urls')),
    path('clientes/', include('clientes.urls')),
    path('cobranza/', include('cobranza.urls')),
    path('chatbot/', include('chatbot.urls')), 
    path('notificaciones/', include('notificaciones.urls')),
    path('reportes/', include('reportes.urls')),  # ← Agregar esta línea
]