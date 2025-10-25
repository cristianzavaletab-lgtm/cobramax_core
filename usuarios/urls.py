from django.urls import path
from . import views

urlpatterns = [
    # Página unificada de autenticación y registro en la raíz
    path('', views.unified_auth, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # legacy: keep login/ path pointing to unified view as well
    path('login/', views.unified_auth, name='login_alt'),
    # Aprobación de cobradores
    path('cobradores/pendientes/', views.pending_cobradores, name='pending_cobradores'),
    path('cobradores/approve/<int:user_id>/', views.approve_cobrador, name='approve_cobrador'),
    path('cobradores/reject/<int:user_id>/', views.reject_cobrador, name='reject_cobrador'),
]