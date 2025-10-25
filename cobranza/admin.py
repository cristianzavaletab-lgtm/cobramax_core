# cobranza/admin.py
from django.contrib import admin
from .models import Pago, Transaccion

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('codigo_transaccion', 'cliente', 'monto', 'metodo_pago', 'estado', 'fecha_pago', 'validado_por')
    list_filter = ('estado', 'metodo_pago', 'fecha_pago')
    search_fields = ('codigo_transaccion', 'cliente__usuario__first_name', 'cliente__usuario__last_name', 'cliente__dni')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion', 'codigo_transaccion')
    list_editable = ('estado',)
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('cliente', 'monto', 'metodo_pago', 'estado', 'fecha_pago')
        }),
        ('Validación', {
            'fields': ('validado_por', 'fecha_validacion', 'comprobante', 'observaciones')
        }),
        ('Información de Transacción', {
            'fields': ('codigo_transaccion', 'registrado_por')
        }),
        ('Auditoría', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        
        # Si se valida el pago, registrar quien lo validó y cuando
        if obj.estado == 'completado' and not obj.validado_por:
            obj.validado_por = request.user
            obj.fecha_validacion = timezone.now()
        
        super().save_model(request, obj, form, change)

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'monto', 'saldo_anterior', 'saldo_posterior', 'fecha_transaccion')
    list_filter = ('tipo', 'fecha_transaccion')
    search_fields = ('cliente__usuario__first_name', 'cliente__usuario__last_name', 'cliente__dni')
    readonly_fields = ('fecha_transaccion',)
    
    def has_add_permission(self, request):
        # Las transacciones se crean automáticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Las transacciones no se pueden editar (son de auditoría)
        return False