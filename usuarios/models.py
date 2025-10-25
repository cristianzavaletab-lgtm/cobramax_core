# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class ActionLog(models.Model):
    """Registro simple de acciones para auditoría (aprobar/rechazar usuarios, etc.)"""
    ACTION_CHOICES = [
        ('approve_cobrador', 'Aprobar cobrador'),
        ('reject_cobrador', 'Rechazar cobrador'),
        ('other', 'Otro'),
    ]

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='acciones_realizadas')
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='acciones_recibidas')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default='other')
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Acción'
        verbose_name_plural = 'Registros de Acciones'
        ordering = ['-timestamp']

    def __str__(self):
        actor = self.actor.username if self.actor else 'Sistema'
        target = self.target_user.username if self.target_user else '---'
        return f"{self.get_action_display()} por {actor} sobre {target} - {self.timestamp}"

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('oficina', 'Oficina'),
        ('cobrador', 'Cobrador'),
        ('cliente', 'Cliente'),
    ]
    
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True, default="")
    direccion = models.TextField(blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_tipo_usuario_display()}"