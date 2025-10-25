# notificaciones/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import logging
from .models import Notificacion, PlantillaNotificacion
from clientes.models import Cliente
from .services import NotificacionService

logger = logging.getLogger(__name__)

@shared_task
def enviar_notificaciones_pendientes():
    """Enviar notificaciones pendientes programadas"""
    try:
        notificaciones = Notificacion.objects.filter(
            Q(estado='pendiente') | Q(estado='programado'),
            Q(programada_para__isnull=True) | Q(programada_para__lte=timezone.now())
        )
        
        service = NotificacionService()
        enviadas = 0
        fallidas = 0
        
        for notificacion in notificaciones:
            resultado = service.enviar_notificacion(notificacion)
            if resultado.get('success'):
                enviadas += 1
            else:
                fallidas += 1
        
        logger.info(f"Tarea notificaciones: {enviadas} enviadas, {fallidas} fallidas")
        return {'enviadas': enviadas, 'fallidas': fallidas}
        
    except Exception as e:
        logger.error(f"Error en tarea notificaciones: {str(e)}")
        return {'error': str(e)}

@shared_task
def enviar_recordatorios_pago_automaticos():
    """Enviar recordatorios automáticos a clientes morosos"""
    try:
        clientes_morosos = Cliente.objects.filter(
            estado='moroso',
            deuda_actual__gt=0,
            # Excluir clientes con notificación reciente (últimos 3 días)
            notificaciones__tipo='recordatorio_pago',
            notificaciones__creada_en__gte=timezone.now() - timedelta(days=3)
        ).exclude(
            # Excluir por condición específica si es necesario
        ).distinct()
        
        service = NotificacionService()
        enviadas = 0
        
        for cliente in clientes_morosos:
            notificacion = service.crear_notificacion_automatica(
                tipo='recordatorio_pago',
                cliente=cliente,
                canal='whatsapp'
            )
            
            if notificacion:
                resultado = service.enviar_notificacion(notificacion)
                if resultado.get('success'):
                    enviadas += 1
        
        logger.info(f"Recordatorios automáticos: {enviadas} enviados")
        return {'enviadas': enviadas}
        
    except Exception as e:
        logger.error(f"Error en recordatorios automáticos: {str(e)}")
        return {'error': str(e)}

@shared_task
def enviar_confirmaciones_pago_automaticas(cliente_id, monto_pagado):
    """Enviar confirmación automática después de un pago"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        service = NotificacionService()
        notificacion = service.crear_notificacion_automatica(
            tipo='pago_confirmado',
            cliente=cliente,
            canal='whatsapp'
        )
        
        if notificacion:
            # Personalizar mensaje con el monto pagado
            notificacion.mensaje = notificacion.mensaje.replace('{monto_pagado}', f"S/ {monto_pagado}")
            notificacion.save()
            
            resultado = service.enviar_notificacion(notificacion)
            return {'success': resultado.get('success'), 'cliente': cliente.nombre_completo}
        
        return {'success': False, 'error': 'No se pudo crear notificación'}
        
    except Exception as e:
        logger.error(f"Error en confirmación de pago: {str(e)}")
        return {'error': str(e)}

@shared_task
def limpiar_notificaciones_antiguas():
    """Limpiar notificaciones antiguas (más de 90 días)"""
    try:
        fecha_limite = timezone.now() - timedelta(days=90)
        eliminadas = Notificacion.objects.filter(
            creada_en__lt=fecha_limite
        ).count()
        
        Notificacion.objects.filter(
            creada_en__lt=fecha_limite
        ).delete()
        
        logger.info(f"Notificaciones limpiadas: {eliminadas} eliminadas")
        return {'eliminadas': eliminadas}
        
    except Exception as e:
        logger.error(f"Error limpiando notificaciones: {str(e)}")
        return {'error': str(e)}

@shared_task
def reporte_estado_notificaciones():
    """Generar reporte diario de estado de notificaciones"""
    try:
        from datetime import datetime
        
        # Estadísticas del día
        hoy = timezone.now().date()
        notificaciones_hoy = Notificacion.objects.filter(
            creada_en__date=hoy
        )
        
        total = notificaciones_hoy.count()
        enviadas = notificaciones_hoy.filter(estado='enviado').count()
        fallidas = notificaciones_hoy.filter(estado='fallido').count()
        
        # Aquí podrías enviar un email con el reporte
        logger.info(f"Reporte notificaciones {hoy}: Total={total}, Enviadas={enviadas}, Fallidas={fallidas}")
        
        return {
            'fecha': hoy.isoformat(),
            'total': total,
            'enviadas': enviadas,
            'fallidas': fallidas
        }
        
    except Exception as e:
        logger.error(f"Error en reporte notificaciones: {str(e)}")
        return {'error': str(e)}


@shared_task
def enviar_mensaje_directo(canal, telefono=None, email=None, mensaje='', usuario_id=None):
    """Enviar un mensaje ad-hoc usando NotificacionService (sin crear modelo Notificacion).

    Esta tarea facilita pruebas y encolado desde la UI de test.
    """
    try:
        service = NotificacionService()
        if canal == 'whatsapp':
            return service.whatsapp_service.enviar_mensaje(telefono, mensaje)
        elif canal == 'email':
            return service.email_service.enviar_email(email, 'Prueba Cobramax', mensaje, html_message=None)
        elif canal == 'sms':
            return service.sms_service.enviar_sms(telefono, mensaje)
        else:
            return {'success': False, 'error': f'Canal no soportado: {canal}'}
    except Exception as e:
        logger.error(f"Error en tarea enviar_mensaje_directo: {e}")
        return {'success': False, 'error': str(e)}