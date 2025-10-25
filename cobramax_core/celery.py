# cobramax_core/celery.py (actualizar)
from celery import Celery
import os
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cobramax_core.settings')

app = Celery('cobramax_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tareas programadas
app.conf.beat_schedule = {
    'enviar-notificaciones-pendientes': {
        'task': 'notificaciones.tasks.enviar_notificaciones_pendientes',
        'schedule': 300.0,  # Cada 5 minutos
    },
    'recordatorios-pago-automaticos': {
        'task': 'notificaciones.tasks.enviar_recordatorios_pago_automaticos',
        'schedule': 86400.0,  # Diario
    },
    'limpiar-notificaciones-antiguas': {
        'task': 'notificaciones.tasks.limpiar_notificaciones_antiguas',
        'schedule': 604800.0,  # Semanal
    },
    'reporte-estado-notificaciones': {
        'task': 'notificaciones.tasks.reporte_estado_notificaciones',
        'schedule': 86400.0,  # Diario
    },
    # Ejecutar ciclo de cobranza diariamente a las 00:05 para marcar en riesgo/corte según el día
    'mark-cobranza-cycle': {
        'task': 'cobranza.tasks.mark_cobranza_cycle_task',
        'schedule': crontab(hour=0, minute=5),
    },
}