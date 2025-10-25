from django.core.management.base import BaseCommand
from django.utils import timezone
from clientes.models import Cliente
from cobranza.models import CorteRegistro

class Command(BaseCommand):
    help = 'Marca clientes en riesgo o cortados según el día del mes y su deuda'

    def handle(self, *args, **options):
        today = timezone.localdate()
        day = today.day
        self.stdout.write(f"Ejecutando ciclo de cobranza para día {day}")

        # Periodo 8-10: marcar en riesgo (usamos estado 'moroso' para señalizar)
        if 8 <= day <= 10:
            clientes = Cliente.objects.filter(estado='activo', deuda_actual__gt=0)
            for c in clientes:
                c.estado = 'moroso'
                c.save()
                CorteRegistro.objects.create(
                    cliente=c,
                    tipo='alerta',
                    detalle=f'Marcado en riesgo por fecha del mes ({day})',
                    creado_por=None
                )
            self.stdout.write(self.style.SUCCESS(f'Marcados {clientes.count()} clientes como en riesgo'))

        # Después del día 10: marcar cortados (suspendido)
        if day > 10:
            clientes = Cliente.objects.filter(deuda_actual__gt=0).exclude(estado='suspendido')
            count = 0
            for c in clientes:
                if c.estado != 'suspendido':
                    c.estado = 'suspendido'
                    c.save()
                    CorteRegistro.objects.create(
                        cliente=c,
                        tipo='corte',
                        detalle=f'Servicio cortado por falta de pago (día {day})',
                        creado_por=None
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Cortados {count} clientes'))

        if day < 8:
            self.stdout.write('No hay acciones programadas antes del día 8')
*** End Patch