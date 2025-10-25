# zonas/models.py
from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class Zona(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, default="")
    codigo = models.CharField(max_length=10, unique=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    cobrador = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'tipo_usuario': 'cobrador'}
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    def total_clientes(self):
        """Número total de clientes en esta zona"""
        try:
            # Esto funcionará cuando tengamos el modelo Cliente
            return self.cliente_set.count()
        except:
            # Por ahora retornar 0 hasta que creemos el modelo Cliente
            return 0
    
    def cobrador_actual(self):
        return self.cobrador.get_full_name() if self.cobrador else "Sin asignar"


class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'

    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='provincias')
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('departamento', 'nombre')
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'

    def __str__(self):
        return f"{self.nombre} ({self.departamento.nombre})"


class Distrito(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='distritos')
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('provincia', 'nombre')
        verbose_name = 'Distrito'
        verbose_name_plural = 'Distritos'

    def __str__(self):
        return f"{self.nombre} ({self.provincia.nombre})"


class Caserio(models.Model):
    distrito = models.ForeignKey(Distrito, on_delete=models.CASCADE, related_name='caserios')
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, blank=True, default='')
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('distrito', 'nombre')
        verbose_name = 'Caserío'
        verbose_name_plural = 'Caseríos'

    def __str__(self):
        return f"{self.nombre} - {self.distrito.nombre} / {self.distrito.provincia.nombre}"