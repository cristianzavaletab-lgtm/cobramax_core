# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Chatbot público (para clientes)
    path('', views.chatbot_interface, name='chatbot_interface'),
    path('buscar/', views.buscar_respuesta, name='buscar_respuesta'),
    path('iniciar-conversacion/', views.iniciar_conversacion, name='iniciar_conversacion'),
    path('send/', views.chatbot_send, name='chatbot_send'),
    path('history/<int:conversacion_id>/', views.chatbot_history, name='chatbot_history'),
    
    # Gestión de preguntas frecuentes
    path('preguntas-frecuentes/', views.gestion_preguntas_frecuentes, name='gestion_preguntas_frecuentes'),
    path('preguntas/agregar/', views.agregar_pregunta_frecuente, name='agregar_pregunta_frecuente'),
    path('preguntas/editar/<int:pregunta_id>/', views.editar_pregunta_frecuente, name='editar_pregunta_frecuente'),
    path('preguntas/toggle/<int:pregunta_id>/', views.toggle_pregunta_frecuente, name='toggle_pregunta_frecuente'),
    
    # Gestión de tickets
    path('tickets/', views.dashboard_tickets, name='dashboard_tickets'),
    path('tickets/crear/', views.crear_ticket_manual, name='crear_ticket_manual'),
    # Endpoint AJAX para crear ticket desde la UI del chatbot
    path('tickets/crear-ajax/', views.chatbot_create_ticket, name='chatbot_create_ticket'),
]