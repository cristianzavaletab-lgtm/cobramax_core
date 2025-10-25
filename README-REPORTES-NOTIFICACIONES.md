Resumen rápido — Cómo probar Reportes (móvil) y Notificaciones + Celery (desarrollo)

1) Requisitos
- Python 3.11
- Redis (local o vía docker-compose)
- Virtualenv recomendado

2) Variables de entorno (archivo `.env`) — valores de ejemplo
DJANGO_SETTINGS_MODULE=cobramax_core.settings
DATABASE_URL=postgres://cobramax_user:password123@localhost:5432/cobramax_db
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@cobramax.local

3) Levantar Redis con docker-compose (desarrollo)
- Desde la carpeta del proyecto:
  docker-compose up redis

4) Ejecutar Celery (local)
- Instala dependencias y ejecuta en una terminal:
  pip install -r requirements.txt
  celery -A cobramax_core worker --loglevel=info
- Para beat (tareas periódicas):
  celery -A cobramax_core beat --loglevel=info

5) Probar notificaciones (entorno de dev)
- Si no configuras Twilio, `NotificacionService` simulará envíos y los mostrará en consola.
- Hay una vista de prueba: `/notificaciones/test-send/` (acceso autenticado) para enviar WhatsApp o Email de prueba.

6) Integración real con Twilio (WhatsApp)
- Instala la librería Twilio en tu virtualenv:
  ```powershell
  .\venv_cobramax\Scripts\Activate.ps1
  pip install twilio
  pip freeze > requirements.txt
  ```
- Configura las variables en tu `.env` (usa `.env.example` como guía):
  - `TWILIO_ACCOUNT_SID` (ej. AC...)
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_WHATSAPP_NUMBER` (ej. +1415xxxxxxx - número sandbox de Twilio)
- Para el sandbox de Twilio: en la consola Twilio → Messaging → Try WhatsApp Sandbox, sigue las instrucciones para unir tu teléfono.
- Luego prueba desde la UI `/notificaciones/test-send/` (selecciona WhatsApp y envía). Si todo está correcto verás en la respuesta JSON `id_externo` con el SID del mensaje.

6) Móvil / Responsividad
- Las plantillas usan Bootstrap 5 y meta viewport; los gráficos Chart.js trabajan en modo `responsive:true`.
- Si quieres un build específico para AMP o PWA, lo añadimos como siguiente paso.

7) Siguientes pasos recomendados
- Proveer claves Twilio en `.env` para envíos reales.
- Configurar SMTP (SMTP_HOST, SMTP_USER) si quieres usar email real.
- Añadir CI que levante Redis y ejecute tests con Celery tasks mocked.
