# notificaciones/management/commands/crear_configuraciones.py
from django.core.management.base import BaseCommand
from notificaciones.models import ConfiguracionNotificacion

class Command(BaseCommand):
    help = 'Crea configuraciones predeterminadas para notificaciones'

    def handle(self, *args, **options):
        configuraciones = [
            ('TWILIO_ACCOUNT_SID', '', 'Account SID de Twilio'),
            ('TWILIO_AUTH_TOKEN', '', 'Auth Token de Twilio'),
            ('TWILIO_WHATSAPP_NUMBER', '', 'Número de WhatsApp de Twilio'),
            ('EMAIL_HOST', '', 'Servidor SMTP para emails'),
            ('RECORDATORIO_DIAS_ANTES', '3', 'Días antes para recordatorios de pago'),
            ('NOTIFICACIONES_ACTIVAS', 'true', 'Activar/desactivar notificaciones automáticas'),
        ]
        
        creadas = 0
        for clave, valor, descripcion in configuraciones:
            if not ConfiguracionNotificacion.objects.filter(clave=clave).exists():
                ConfiguracionNotificacion.objects.create(
                    clave=clave,
                    valor=valor,
                    descripcion=descripcion
                )
                creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Configuración creada: {clave}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {creadas} configuraciones predeterminadas')
        )