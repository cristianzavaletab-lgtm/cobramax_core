from django.conf import settings
from django.db import models


class Cliente(models.Model):
    """Modelo Cliente (definición basada en la migración inicial).

    Mantengo los nombres de campo y las opciones tal como aparecen en
    `clientes/migrations/0001_initial.py` para mantener compatibilidad con
    la base de datos ya creada.
    """

    DNI_MAX_LENGTH = 8
    RUC_MAX_LENGTH = 11

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('moroso', 'Moroso'),
        ('suspendido', 'Suspendido'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo_usuario': 'cliente'},
    )
    # Campos añadidos para compatibilidad con formularios y templates antiguos
    nombre = models.CharField(max_length=100, blank=True, default='')
    apellido = models.CharField(max_length=100, blank=True, default='')
    dni = models.CharField(max_length=DNI_MAX_LENGTH, unique=True, verbose_name='DNI')
    ruc = models.CharField(max_length=RUC_MAX_LENGTH, blank=True, verbose_name='RUC')
    telefono_principal = models.CharField(max_length=15)
    telefono_secundario = models.CharField(max_length=15, blank=True)
    # campo de compatibilidad (muchas plantillas usan cliente.telefono)
    telefono = models.CharField(max_length=15, blank=True, default='')
    direccion = models.TextField()
    referencia = models.TextField(blank=True, verbose_name='Referencia de domicilio')
    fecha_instalacion = models.DateField(verbose_name='Fecha de instalación')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    plan_contratado = models.CharField(max_length=100, default='Plan Básico')
    # campo de compatibilidad `plan` (plantillas usan cliente.plan)
    plan = models.CharField(max_length=100, blank=True, default='')
    # email independiente (opcional) para compatibilidad; normalmente viene del User
    email = models.EmailField(blank=True, default='')
    velocidad = models.CharField(max_length=50, default='10 Mbps')
    deuda_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=100.0)
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    dia_vencimiento = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='clientes_creados',
        limit_choices_to={'tipo_usuario__in': ['admin', 'oficina']},
    )

    zona = models.ForeignKey(
        'zonas.Zona',
        on_delete=models.PROTECT,
        verbose_name='Zona asignada',
    )

    # Nuevo: referencia opcional a caserío (jerarquía más fina)
    caserio = models.ForeignKey(
        'zonas.Caserio',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name='Caserío asignado'
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['usuario__first_name', 'usuario__last_name']
        indexes = [
            models.Index(fields=['dni'], name='clientes_cl_dni_5e5da9_idx'),
            models.Index(fields=['estado'], name='clientes_cl_estado_54796b_idx'),
            models.Index(fields=['zona'], name='clientes_cl_zona_id_5f7775_idx'),
        ]

    def __str__(self):
        return self.nombre_completo()

    def nombre_completo(self):
        # Intentar usar get_full_name del user model, si existe y devuelve algo
        try:
            full = getattr(self.usuario, 'get_full_name', None)
            if callable(full):
                name = full()
                if name:
                    return name
        except Exception:
            pass
        # Fallback con first_name/last_name
        first = getattr(self.usuario, 'first_name', '') or ''
        last = getattr(self.usuario, 'last_name', '') or ''
        return f"{first} {last}".strip()

    def cobrador_asignado(self):
        # Dejar una referencia segura a cobrador si existe en la zona
        try:
            return getattr(self.zona, 'cobrador', None)
        except Exception:
            return None

    # Nota: Ya no usamos propiedades Python para compatibilidad; los
    # campos están presentes en la BD como columnas reales.
