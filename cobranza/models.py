# cobranza/models.py
from django.db import models
from django.contrib.auth import get_user_model
from clientes.models import Cliente

Usuario = get_user_model()

class Pago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
        ('revertido', 'Revertido'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('yape', 'Yape'),
        ('plin', 'Plin'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('deposito', 'Depósito'),
    ]
    
    # Información básica
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    
    # Información de transacción
    codigo_transaccion = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_pago = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Validación y comprobante
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    observaciones = models.TextField(blank=True)
    validado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pagos_validados',
        limit_choices_to={'tipo_usuario__in': ['admin', 'oficina']}
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    
    # Auditoría
    registrado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='pagos_registrados'
    )
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['cliente', 'fecha_pago']),
            models.Index(fields=['estado']),
            models.Index(fields=['codigo_transaccion']),
        ]
    
    def __str__(self):
        return f"Pago {self.codigo_transaccion} - {self.cliente} - S/ {self.monto}"
    
    def save(self, *args, **kwargs):
        if not self.codigo_transaccion:
            # Generar código único automáticamente
            import uuid
            self.codigo_transaccion = f"PAGO-{uuid.uuid4().hex[:8].upper()}"
        
        # Si el pago se marca como completado, actualizar la deuda del cliente
        if self.estado == 'completado' and self.pk:
            original = Pago.objects.get(pk=self.pk)
            if original.estado != 'completado':
                self.cliente.deuda_actual -= self.monto
                self.cliente.save()
        
        super().save(*args, **kwargs)
    
    def puede_editar(self):
        """Determina si el pago puede ser editado"""
        return self.estado in ['pendiente', 'rechazado']
    
    def puede_validar(self):
        """Determina si el pago puede ser validado"""
        return self.estado == 'pendiente' and self.validado_por is None

class Transaccion(models.Model):
    """Historial de transacciones para auditoría"""
    TIPO_CHOICES = [
        ('pago', 'Pago'),
        ('ajuste', 'Ajuste'),
        ('cargo', 'Cargo'),
    ]
    
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-fecha_transaccion']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} - S/ {self.monto}"


class CorteRegistro(models.Model):
    TIPO_CHOICES = [
        ('alerta', 'Alerta En Riesgo'),
        ('corte', 'Corte'),
        ('reconexion', 'Reconexión'),
    ]

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    detalle = models.TextField(blank=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Corte / Evento'
        verbose_name_plural = 'Cortes / Eventos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} - {self.fecha}"


# Señales: reconectar cliente si el pago se completa y la deuda queda en 0
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Pago)
def pago_post_save_update_cliente(sender, instance, created, **kwargs):
    try:
        # Si el pago está completado, actualizar estado del cliente si procede
        if instance.estado == 'completado':
            cliente = instance.cliente
            # actualizar deuda ya ocurre en save(), pero verificamos estado
            if cliente.deuda_actual <= 0 and cliente.estado in ['suspendido', 'moroso']:
                cliente.estado = 'activo'
                cliente.save()
                CorteRegistro.objects.create(
                    cliente=cliente,
                    tipo='reconexion',
                    detalle=f'Reconexión automática al registrar pago {instance.codigo_transaccion}',
                    creado_por=instance.validado_por if instance.validado_por and instance.validado_por.tipo_usuario in ['admin','oficina'] else None
                )
    except Exception:
        # No dejar que una señal rompa el flujo de guardado
        pass