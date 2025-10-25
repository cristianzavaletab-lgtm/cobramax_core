# notificaciones/models.py
from django.db import models
from django.conf import settings
from clientes.models import Cliente
from zonas.models import Zona
from django.utils import timezone


class PlantillaNotificacion(models.Model):
    """Plantillas predefinidas para notificaciones"""
    
    TIPO_CHOICES = [
        ('pago', 'Recordatorio de Pago'),
        ('vencimiento', 'Aviso de Vencimiento'),
        ('confirmacion', 'Confirmación de Pago'),
        ('promocion', 'Promoción'),
        ('soporte', 'Soporte Técnico'),
        ('general', 'Mensaje General'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Plantilla")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    contenido = models.TextField(verbose_name="Contenido", help_text="Puedes usar variables como {{nombre}}, {{monto}}, etc.")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='plantillas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Notificación"
        verbose_name_plural = "Plantillas de Notificaciones"
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class Notificacion(models.Model):
    """Notificaciones enviadas a clientes"""
    
    TIPO_CHOICES = [
        ('pago', 'Recordatorio de Pago'),
        ('vencimiento', 'Aviso de Vencimiento'),
        ('confirmacion', 'Confirmación de Pago'),
        ('promocion', 'Promoción'),
        ('soporte', 'Soporte Técnico'),
        ('general', 'Mensaje General'),
    ]
    
    CANAL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Correo Electrónico'),
        ('sms', 'SMS'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
        ('leido', 'Leído'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notificaciones')
    zona = models.ForeignKey(Zona, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    mensaje = models.TextField(verbose_name="Mensaje")
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, default='whatsapp', verbose_name="Canal")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    plantilla = models.ForeignKey(PlantillaNotificacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones')
    
    # Metadata
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notificaciones_enviadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Datos adicionales
    destinatario_telefono = models.CharField(max_length=20, blank=True, null=True)
    destinatario_email = models.EmailField(blank=True, null=True)
    error_mensaje = models.TextField(blank=True, null=True, verbose_name="Mensaje de Error")
    intentos_envio = models.IntegerField(default=0, verbose_name="Intentos de Envío")
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nombre_completo} ({self.estado})"
    
    def enviar_notificacion(self):
        """Simula el envío de la notificación"""
        self.intentos_envio += 1
        
        try:
            # Aquí iría la lógica real de envío según el canal
            if self.canal == 'whatsapp':
                # Lógica de envío por WhatsApp (Twilio, etc.)
                self.destinatario_telefono = self.cliente.telefono
                exito = True  # Simulación
            elif self.canal == 'email':
                # Lógica de envío por email
                self.destinatario_email = self.cliente.email
                exito = True  # Simulación
            elif self.canal == 'sms':
                # Lógica de envío por SMS
                self.destinatario_telefono = self.cliente.telefono
                exito = True  # Simulación
            else:
                exito = False
            
            if exito:
                self.estado = 'enviado'
                self.fecha_envio = timezone.now()
                self.error_mensaje = None
            else:
                self.estado = 'fallido'
                self.error_mensaje = 'Canal de envío no válido'
            
            self.save()
            
            # Registrar el intento
            RegistroEnvio.objects.create(
                notificacion=self,
                exitoso=exito,
                mensaje_error=self.error_mensaje if not exito else None
            )
            
            return exito
            
        except Exception as e:
            self.estado = 'fallido'
            self.error_mensaje = str(e)
            self.save()
            
            # Registrar el intento fallido
            RegistroEnvio.objects.create(
                notificacion=self,
                exitoso=False,
                mensaje_error=str(e)
            )
            
            return False
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if self.estado == 'enviado':
            self.estado = 'leido'
            self.fecha_lectura = timezone.now()
            self.save()


class RegistroEnvio(models.Model):
    """Registro de intentos de envío de notificaciones"""
    
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name='registros_envio')
    fecha_intento = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField(default=False)
    mensaje_error = models.TextField(blank=True, null=True)
    respuesta_api = models.TextField(blank=True, null=True, verbose_name="Respuesta de la API")
    
    class Meta:
        verbose_name = "Registro de Envío"
        verbose_name_plural = "Registros de Envío"
        ordering = ['-fecha_intento']
    
    def __str__(self):
        estado = "Exitoso" if self.exitoso else "Fallido"
        return f"{estado} - {self.notificacion} - {self.fecha_intento.strftime('%d/%m/%Y %H:%M')}"