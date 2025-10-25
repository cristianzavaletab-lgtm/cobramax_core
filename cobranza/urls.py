# cobranza/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pagos, name='lista_pagos'),
    path('registrar/', views.registrar_pago, name='registrar_pago'),
    path('registrar/<int:cliente_id>/', views.registrar_pago, name='registrar_pago_cliente'),
    path('<int:pago_id>/', views.detalle_pago, name='detalle_pago'),
    path('<int:pago_id>/validar/', views.validar_pago, name='validar_pago'),
]