# reportes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_reportes, name='dashboard_reportes'),
    path('ingresos/', views.reporte_ingresos, name='reporte_ingresos'),
    path('morosos/', views.reporte_morosos, name='reporte_morosos'),
    path('clientes/', views.reporte_clientes, name='reporte_clientes'),
    path('zonas/', views.reporte_zonas, name='reporte_zonas'),
    # API endpoints para gráficos y mapas
    path('api/ingresos-por-dia/', views.api_ingresos_por_dia, name='api_ingresos_por_dia'),
    path('api/clientes-por-zona/', views.api_clientes_por_zona, name='api_clientes_por_zona'),
    path('api/metodos-pago/', views.api_metodos_pago, name='api_metodos_pago'),
    path('api/zonas-geo/', views.api_zonas_geo, name='api_zonas_geo'),
]