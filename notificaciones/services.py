# notificaciones/services.py (versión segura)
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

# Intentar importar requests, pero continuar sin ella si no está disponible
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("La librería 'requests' no está instalada. Algunas funciones pueden no estar disponibles.")

# Intentar importar el cliente de Twilio (opcional)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except Exception:
    TwilioClient = None
    TWILIO_AVAILABLE = False

class WhatsAppService:
    """Servicio para enviar mensajes por WhatsApp"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '')
    
    def enviar_mensaje(self, telefono, mensaje):
        """
        Enviar mensaje por WhatsApp usando Twilio API
        """
        try:
            # Si no hay credenciales completas, continuar simulando
            if not all([self.account_sid, self.auth_token, self.whatsapp_number]):
                logger.warning("Credenciales de Twilio no configuradas. Simulando envío.")
                return self._simular_envio(telefono, mensaje)

            # Si la librería de Twilio está disponible, usarla
            if TWILIO_AVAILABLE and TwilioClient is not None:
                try:
                    client = TwilioClient(self.account_sid, self.auth_token)
                    # Twilio espera números en formato E.164 y el prefijo 'whatsapp:' para WhatsApp
                    to_number = telefono if telefono.startswith('+') else f'+{telefono}'
                    message = client.messages.create(
                        body=mensaje,
                        from_=f'whatsapp:{self.whatsapp_number}',
                        to=f'whatsapp:{to_number}'
                    )
                    logger.info(f"WhatsApp enviado via Twilio SID={message.sid} status={getattr(message, 'status', None)}")
                    return {
                        'success': True,
                        'id_externo': getattr(message, 'sid', None),
                        'estado': getattr(message, 'status', None) or 'queued'
                    }
                except Exception as e:
                    logger.error(f"Error enviando WhatsApp con Twilio: {e}")
                    # si falla con Twilio, retornar fallo en vez de simular para visibilidad
                    return {'success': False, 'error': str(e)}

            # Si llegamos aquí (Twilio no disponible) simular envío
            logger.warning("Twilio no disponible en el entorno. Simulando envío de WhatsApp.")
            return self._simular_envio(telefono, mensaje)
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _simular_envio(self, telefono, mensaje):
        """Simular envío para desarrollo"""
        logger.info(f"SIMULACIÓN WhatsApp a {telefono}: {mensaje}")
        return {
            'success': True, 
            'id_externo': f'sim-{timezone.now().timestamp()}',
            'estado': 'delivered'
        }

# ... (el resto del código de services.py permanece igual)
class EmailService:
    """Servicio para enviar emails"""
    
    def enviar_email(self, destinatario, asunto, mensaje, html_message=None):
        try:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cobramax.com'),
                recipient_list=[destinatario],
                html_message=html_message,
                fail_silently=False,
            )
            return {'success': True, 'id_externo': f'email-{timezone.now().timestamp()}'}
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return {'success': False, 'error': str(e)}

class SMSService:
    """Servicio para enviar SMS (usando Twilio)"""
    
    def enviar_sms(self, telefono, mensaje):
        try:
            # Simulación
            logger.info(f"SIMULACIÓN SMS a {telefono}: {mensaje}")
            return {
                'success': True,
                'id_externo': f'sms-sim-{timezone.now().timestamp()}',
                'estado': 'sent'
            }
        except Exception as e:
            logger.error(f"Error enviando SMS: {str(e)}")
            return {'success': False, 'error': str(e)}

class NotificacionService:
    """Servicio principal para gestionar notificaciones"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    def enviar_notificacion(self, notificacion):
        """
        Enviar una notificación específica
        """
        try:
            # Validar que se pueda enviar
            if not notificacion.puede_enviar:
                return {'success': False, 'error': 'Notificación no está lista para enviar'}
            
            # Personalizar mensaje
            mensaje_personalizado = self._personalizar_mensaje(
                notificacion.mensaje, 
                notificacion.cliente
            )
            
            # Enviar según el canal
            if notificacion.canal == 'whatsapp':
                resultado = self.whatsapp_service.enviar_mensaje(
                    notificacion.cliente.telefono_principal,
                    mensaje_personalizado
                )
            elif notificacion.canal == 'email':
                resultado = self.email_service.enviar_email(
                    notificacion.cliente.email,
                    notificacion.asunto,
                    mensaje_personalizado
                )
            elif notificacion.canal == 'sms':
                resultado = self.sms_service.enviar_sms(
                    notificacion.cliente.telefono_principal,
                    mensaje_personalizado
                )
            else:
                return {'success': False, 'error': f'Canal no soportado: {notificacion.canal}'}
            
            # Actualizar estado de la notificación
            if resultado.get('success'):
                notificacion.estado = 'enviado'
                notificacion.enviada_en = timezone.now()
                notificacion.id_externo = resultado.get('id_externo')
                notificacion.error = None
            else:
                notificacion.estado = 'fallido'
                notificacion.error = resultado.get('error', 'Error desconocido')
            
            notificacion.save()
            return resultado
            
        except Exception as e:
            logger.error(f"Error en enviar_notificacion: {str(e)}")
            notificacion.estado = 'fallido'
            notificacion.error = str(e)
            notificacion.save()
            return {'success': False, 'error': str(e)}
    
    def _personalizar_mensaje(self, mensaje, cliente):
        """Personalizar el mensaje con variables del cliente"""
        variables = {
            '{nombre}': cliente.nombre_completo,
            '{deuda}': f"S/ {cliente.deuda_actual}",
            '{servicio}': cliente.tipo_servicio or 'servicio',
            '{fecha_limite}': (timezone.now() + timezone.timedelta(days=5)).strftime('%d/%m/%Y'),
            '{zona}': cliente.zona.nombre,
            '{cobrador}': cliente.cobrador_asignado.get_full_name() if cliente.cobrador_asignado else 'nuestro cobrador',
        }
        
        mensaje_personalizado = mensaje
        for variable, valor in variables.items():
            mensaje_personalizado = mensaje_personalizado.replace(variable, str(valor))
        
        return mensaje_personalizado
    
    def crear_notificacion_automatica(self, tipo, cliente, canal='whatsapp', programada_para=None):
        """Crear notificación automática basada en plantillas"""
        try:
            from .models import PlantillaNotificacion
            
            plantilla = PlantillaNotificacion.objects.filter(
                tipo=tipo, 
                canal=canal, 
                activa=True
            ).first()
            
            if not plantilla:
                logger.warning(f"No hay plantilla activa para {tipo} en canal {canal}")
                return None
            
            # Obtener usuario del sistema para auditoría
            from django.contrib.auth import get_user_model
            User = get_user_model()
            usuario_sistema = User.objects.filter(is_superuser=True).first()
            
            notificacion = Notificacion(
                tipo=tipo,
                cliente=cliente,
                asunto=plantilla.asunto,
                mensaje=plantilla.mensaje,
                canal=canal,
                programada_para=programada_para,
                creada_por=usuario_sistema or cliente.cobrador_asignado
            )
            
            notificacion.save()
            return notificacion
            
        except Exception as e:
            logger.error(f"Error creando notificación automática: {str(e)}")
            return None