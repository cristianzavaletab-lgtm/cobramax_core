# zonas/admin.py
from django.contrib import admin
from .models import Zona

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'cobrador_actual', 'total_clientes', 'activa')
    list_filter = ('activa', 'cobrador')
    search_fields = ('nombre', 'codigo', 'descripcion')
    list_editable = ('activa',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion')
        }),
        ('Ubicación', {
            'fields': ('latitud', 'longitud')
        }),
        ('Asignación', {
            'fields': ('cobrador', 'activa')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )