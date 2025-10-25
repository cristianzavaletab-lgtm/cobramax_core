# reportes/models.py
from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class ReporteGenerado(models.Model):
    TIPO_REPORTE_CHOICES = [
        ('ingresos', 'Reporte de Ingresos'),
        ('morosos', 'Reporte de Clientes Morosos'),
        ('pagos', 'Reporte de Pagos'),
        ('clientes', 'Reporte de Clientes'),
    ]
    
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE_CHOICES)
    parametros = models.JSONField(default=dict)  # Para guardar filtros aplicados
    archivo = models.FileField(upload_to='reportes/', blank=True, null=True)
    generado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Reporte Generado"
        verbose_name_plural = "Reportes Generados"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}"