# clientes/admin.py
from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre_completo', 'zona', 'estado', 'deuda_actual', 'cobrador_asignado', 'fecha_instalacion')
    list_filter = ('estado', 'zona', 'fecha_instalacion')
    search_fields = ('dni', 'usuario__first_name', 'usuario__last_name', 'direccion')
    list_editable = ('estado',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('usuario', 'dni', 'ruc', 'telefono_principal', 'telefono_secundario')
        }),
        ('Dirección y Ubicación', {
            'fields': ('direccion', 'referencia', 'zona')
        }),
        ('Información del Servicio', {
            'fields': ('fecha_instalacion', 'estado', 'plan_contratado', 'velocidad')
        }),
        ('Información de Cobranza', {
            'fields': ('deuda_actual', 'limite_credito')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)