from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chatbot.models import PreguntaFrecuente

class Command(BaseCommand):
    help = 'Seed initial chatbot preguntas frecuentes'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            self.stdout.write(self.style.WARNING('No hay usuarios en la base de datos. Crea un usuario y vuelve a ejecutar este comando.'))
            return

        defaults = [
            {
                'pregunta': '¿Cómo puedo pagar mi factura?',
                'respuesta': 'Puedes pagar tu factura a través de nuestra plataforma en línea, en agentes autorizados o por transferencia bancaria. Dirígete al menú Cobranza para más opciones.',
                'categoria': 'pagos',
                'palabras_clave': 'pago,factura,transferencia,cuota'
            },
            {
                'pregunta': 'Mi Internet va muy lento, ¿qué hago?',
                'respuesta': 'Prueba reiniciar tu router y verificar las conexiones. Si el problema persiste, abre un ticket de soporte desde el área de clientes.',
                'categoria': 'tecnico',
                'palabras_clave': 'internet,lento,router,conexion,velocidad'
            },
            {
                'pregunta': '¿Cómo cambio mi plan?',
                'respuesta': 'Puedes solicitar un cambio de plan desde el panel de cliente o contactando a soporte. Revisa los planes disponibles en la sección Planes.',
                'categoria': 'servicio',
                'palabras_clave': 'plan,cambio,contrato'
            },
            {
                'pregunta': '¿Cómo actualizo mis datos de contacto?',
                'respuesta': 'Ve a tu perfil y edita tu teléfono y correo. Si necesitas asistencia, contacta a soporte.',
                'categoria': 'cuenta',
                'palabras_clave': 'perfil,telefono,email,direccion'
            },
        ]

        created = 0
        for item in defaults:
            obj, was_created = PreguntaFrecuente.objects.get_or_create(
                pregunta=item['pregunta'],
                defaults={
                    'respuesta': item['respuesta'],
                    'categoria': item['categoria'],
                    'palabras_clave': item['palabras_clave'],
                    'activa': True,
                    'creada_por': user
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Preguntas añadidas: {created}'))
