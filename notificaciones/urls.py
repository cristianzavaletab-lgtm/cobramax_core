# notificaciones/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard y listas
    path('', views.dashboard_notificaciones, name='dashboard_notificaciones'),
    path('lista/', views.lista_notificaciones, name='lista_notificaciones'),
    path('detalle/<int:notificacion_id>/', views.detalle_notificacion, name='detalle_notificacion'),
    
    # Notificaciones individuales
    path('crear/', views.crear_notificacion, name='crear_notificacion'),
    path('reenviar/<int:notificacion_id>/', views.reenviar_notificacion, name='reenviar_notificacion'),
    
    # Notificaciones masivas
    path('masiva/', views.notificacion_masiva, name='notificacion_masiva'),
    
    # Plantillas
    path('plantillas/', views.lista_plantillas, name='lista_plantillas'),
    path('plantillas/crear/', views.crear_plantilla, name='crear_plantilla'),
    path('plantillas/editar/<int:plantilla_id>/', views.editar_plantilla, name='editar_plantilla'),
    path('plantillas/toggle/<int:plantilla_id>/', views.toggle_plantilla, name='toggle_plantilla'),
    
    # API endpoints
    path('api/plantillas/', views.obtener_plantillas_por_tipo, name='api_plantillas'),
    path('api/estadisticas/', views.estadisticas_notificaciones, name='api_estadisticas'),
    path('api/clientes-autocomplete/', views.obtener_clientes_autocomplete, name='api_clientes_autocomplete'),
    # Utilities / testing
    path('test-send/', views.test_send_notification, name='test_send_notification'),
]