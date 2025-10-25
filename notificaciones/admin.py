# notificaciones/admin.py
from django.contrib import admin
from .models import Notificacion, PlantillaNotificacion, RegistroEnvio  # ← Quitar ConfiguracionNotificacion


@admin.register(PlantillaNotificacion)
class PlantillaNotificacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activa', 'creada_por', 'fecha_creacion']
    list_filter = ['tipo', 'activa', 'fecha_creacion']
    search_fields = ['nombre', 'contenido']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']


class RegistroEnvioInline(admin.TabularInline):
    model = RegistroEnvio
    extra = 0
    readonly_fields = ['fecha_intento', 'exitoso', 'mensaje_error', 'respuesta_api']
    can_delete = False


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'tipo', 'canal', 'estado', 'fecha_creacion', 'fecha_envio']
    list_filter = ['tipo', 'canal', 'estado', 'fecha_creacion']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'mensaje']
    readonly_fields = ['fecha_creacion', 'fecha_envio', 'fecha_lectura', 'intentos_envio']
    inlines = [RegistroEnvioInline]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('cliente', 'zona', 'tipo', 'mensaje', 'canal')
        }),
        ('Estado', {
            'fields': ('estado', 'plantilla', 'enviado_por')
        }),
        ('Datos de Envío', {
            'fields': ('destinatario_telefono', 'destinatario_email', 'intentos_envio')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_envio', 'fecha_lectura')
        }),
        ('Errores', {
            'fields': ('error_mensaje',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reenviar_notificaciones']
    
    def reenviar_notificaciones(self, request, queryset):
        exitosas = 0
        fallidas = 0
        
        for notificacion in queryset:
            if notificacion.enviar_notificacion():
                exitosas += 1
            else:
                fallidas += 1
        
        self.message_user(request, f'Reenviadas: {exitosas} exitosas, {fallidas} fallidas')
    
    reenviar_notificaciones.short_description = "Reenviar notificaciones seleccionadas"


@admin.register(RegistroEnvio)
class RegistroEnvioAdmin(admin.ModelAdmin):
    list_display = ['notificacion', 'fecha_intento', 'exitoso', 'mensaje_error']
    list_filter = ['exitoso', 'fecha_intento']
    search_fields = ['notificacion__cliente__nombre', 'mensaje_error']
    readonly_fields = ['notificacion', 'fecha_intento', 'exitoso', 'mensaje_error', 'respuesta_api']