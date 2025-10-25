from celery import shared_task
import logging
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def mark_cobranza_cycle_task(self):
    """Wrapper task to invoke the management command that marks clientes en riesgo/cortados.

    We call the management command to reuse existing logic and ensure single-point maintenance.
    """
    try:
        call_command('mark_cobranza_cycle')
        return {'success': True}
    except Exception as e:
        logger.exception('Error ejecutando mark_cobranza_cycle via Celery')
        # Re-raise to let Celery record failure and retry according to its configuration
        raise
