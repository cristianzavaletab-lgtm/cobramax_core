from django.core.management.base import BaseCommand, CommandError
from notificaciones.services import EmailService

class Command(BaseCommand):
    help = 'Enviar un email de prueba usando la configuración actual (usa EmailService)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Dirección de email destino')
        parser.add_argument('--subject', type=str, default='Prueba de correo - COBRA-MAX')
        parser.add_argument('--message', type=str, default='Este es un correo de prueba enviado desde COBRA-MAX.')

    def handle(self, *args, **options):
        destinatario = options['email']
        asunto = options['subject']
        mensaje = options['message']

        service = EmailService()
        result = service.enviar_email(destinatario, asunto, mensaje)

        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(f'Email enviado correctamente a {destinatario}'))
        else:
            self.stderr.write(self.style.ERROR(f"Error enviando email: {result.get('error')}"))
            raise CommandError('Fallo al enviar email')
