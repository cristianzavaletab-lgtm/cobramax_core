# chatbot/admin.py
from django.contrib import admin
from .models import PreguntaFrecuente, ConversacionChatbot, MensajeChatbot, TicketSoporte, HistorialTicket

@admin.register(PreguntaFrecuente)
class PreguntaFrecuenteAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'categoria', 'veces_consultada', 'activa', 'creada_por', 'creada_en']
    list_filter = ['categoria', 'activa', 'creada_en']
    search_fields = ['pregunta', 'respuesta', 'palabras_clave']
    readonly_fields = ['veces_consultada', 'creada_en', 'actualizada_en']
    list_editable = ['activa']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('pregunta', 'respuesta', 'categoria')
        }),
        ('Configuración de Búsqueda', {
            'fields': ('palabras_clave', 'veces_consultada')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Auditoría', {
            'fields': ('creada_por', 'creada_en', 'actualizada_en'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creada_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(ConversacionChatbot)
class ConversacionChatbotAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'estado', 'fecha_inicio', 'agente_asignado', 'satisfaccion']
    list_filter = ['estado', 'fecha_inicio']
    search_fields = ['cliente__nombre_completo', 'cliente__dni']
    readonly_fields = ['fecha_inicio', 'fecha_fin']
    
    def mensajes_count(self, obj):
        return obj.mensajes.count()
    mensajes_count.short_description = 'Mensajes'

@admin.register(MensajeChatbot)
class MensajeChatbotAdmin(admin.ModelAdmin):
    list_display = ['conversacion', 'tipo', 'contenido_preview', 'timestamp', 'pregunta_relacionada']
    list_filter = ['tipo', 'timestamp']
    search_fields = ['contenido', 'conversacion__cliente__nombre_completo']
    readonly_fields = ['timestamp']
    
    def contenido_preview(self, obj):
        return obj.contenido[:50] + '...' if len(obj.contenido) > 50 else obj.contenido
    contenido_preview.short_description = 'Contenido'

@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'prioridad', 'estado', 'categoria', 'agente_asignado', 'fecha_creacion']
    list_filter = ['prioridad', 'estado', 'categoria', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'conversacion__cliente__nombre_completo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'fecha_cierre']
    list_editable = ['estado', 'prioridad', 'agente_asignado']
    
    fieldsets = (
        ('Información del Ticket', {
            'fields': ('conversacion', 'titulo', 'descripcion', 'categoria')
        }),
        ('Gestión', {
            'fields': ('prioridad', 'estado', 'agente_asignado')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_cierre'),
            'classes': ('collapse',)
        }),
    )

@admin.register(HistorialTicket)
class HistorialTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'usuario', 'accion', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['ticket__titulo', 'usuario__username', 'accion']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False  # El historial se crea automáticamente