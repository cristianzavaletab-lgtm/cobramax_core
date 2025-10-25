# chatbot/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from clientes.models import Cliente

Usuario = get_user_model()

class PreguntaFrecuente(models.Model):
    CATEGORIA_CHOICES = [
        ('pagos', '💳 Pagos y Facturación'),
        ('tecnico', '🔧 Soporte Técnico'),
        ('servicio', '📡 Servicio Internet'),
        ('general', '❓ Consultas Generales'),
        ('cuenta', '👤 Gestión de Cuenta'),
    ]
    
    pregunta = models.CharField(max_length=255)
    respuesta = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='general')
    palabras_clave = models.TextField(help_text="Palabras clave separadas por coma para búsqueda")
    activa = models.BooleanField(default=True)
    veces_consultada = models.PositiveIntegerField(default=0)
    creada_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pregunta Frecuente"
        verbose_name_plural = "Preguntas Frecuentes"
        ordering = ['categoria', 'veces_consultada']
    
    def __str__(self):
        return f"{self.pregunta} ({self.get_categoria_display()})"
    
    def incrementar_consultas(self):
        self.veces_consultada += 1
        self.save(update_fields=['veces_consultada'])

class ConversacionChatbot(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('resuelta', 'Resuelta'),
        ('derivada', 'Derivada a agente'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='conversaciones_chatbot')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    agente_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    satisfaccion = models.IntegerField(null=True, blank=True, help_text="Calificación 1-5")
    
    class Meta:
        verbose_name = "Conversación Chatbot"
        verbose_name_plural = "Conversaciones Chatbot"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Conversación {self.cliente} - {self.fecha_inicio}"

class MensajeChatbot(models.Model):
    TIPO_CHOICES = [
        ('usuario', 'Usuario'),
        ('bot', 'Chatbot'),
        ('agente', 'Agente Humano'),
    ]
    
    conversacion = models.ForeignKey(ConversacionChatbot, on_delete=models.CASCADE, related_name='mensajes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    contenido = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    pregunta_relacionada = models.ForeignKey(PreguntaFrecuente, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Mensaje Chatbot"
        verbose_name_plural = "Mensajes Chatbot"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.contenido[:50]}..."

class TicketSoporte(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', '🟢 Baja'),
        ('media', '🟡 Media'),
        ('alta', '🔴 Alta'),
        ('urgente', '⚡ Urgente'),
    ]
    
    ESTADO_CHOICES = [
        ('abierto', '📝 Abierto'),
        ('en_progreso', '🔨 En Progreso'),
        ('esperando_cliente', '⏳ Esperando Cliente'),
        ('resuelto', '✅ Resuelto'),
        ('cerrado', '🔒 Cerrado'),
    ]
    
    conversacion = models.OneToOneField(ConversacionChatbot, on_delete=models.CASCADE, related_name='ticket')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto')
    categoria = models.CharField(max_length=20, choices=PreguntaFrecuente.CATEGORIA_CHOICES)
    agente_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    creado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tickets_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.titulo}"

class HistorialTicket(models.Model):
    ticket = models.ForeignKey(TicketSoporte, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    accion = models.CharField(max_length=255)
    detalles = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historial de Ticket"
        verbose_name_plural = "Historial de Tickets"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Historial Ticket #{self.ticket.id} - {self.accion}"