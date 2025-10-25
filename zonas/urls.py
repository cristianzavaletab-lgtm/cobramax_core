# zonas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_zonas, name='lista_zonas'),
    path('mapa/', views.mapa_zonas, name='mapa_zonas'),
    path('<int:zona_id>/', views.detalle_zona, name='detalle_zona'),
    # APIs para selects dependientes (públicas)
    path('api/departamentos/', views.api_departamentos, name='api_departamentos'),
    path('api/provincias/<int:departamento_id>/', views.api_provincias, name='api_provincias'),
    path('api/distritos/<int:provincia_id>/', views.api_distritos, name='api_distritos'),
    path('api/caserios/<int:distrito_id>/', views.api_caserios, name='api_caserios'),
]