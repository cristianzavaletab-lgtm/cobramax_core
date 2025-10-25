Settings del Chatbot (COBRA-MAX)

Estos settings configuran el comportamiento del asistente y las políticas de fallback.

- OPENAI_API_KEY (string)
  - Clave de OpenAI (opcional). Si no está presente, el sistema usa búsqueda local en `PreguntaFrecuente`.

- OPENAI_MODEL (string)
  - Modelo por defecto para la API (ej: `gpt-3.5-turbo`). Valor por defecto usado en el código si no se define.

- CHATBOT_RETRY_COUNT (int)
  - Número de reintentos ante errores transitivos de la API externa (default: 2).

- CHATBOT_RETRY_BACKOFF (int | float)
  - Factor de backoff (segundos) entre reintentos. En cada reintento se multiplica por (attempt+1).

- AUTO_TICKET_ON_AI_ERROR (bool)
  - Si True, cuando la llamada al servicio de IA falle completamente, se generará automáticamente un `TicketSoporte` asociado a la `ConversacionChatbot`.

- CHATBOT_RATE_LIMIT (int)
  - Número de mensajes permitidos por ventana de tiempo para cada usuario (ej: 10).

- CHATBOT_RATE_WINDOW (int)
  - Tamaño de la ventana en segundos para el rate limiting (ej: 60).

Notas de despliegue
- Asegúrate de tener `OPENAI_API_KEY` en las variables de entorno si quieres usar la integración con OpenAI.
- Antes de desplegar cambios en modelos (migrations), ejecutar:
  - `python manage.py makemigrations` (si hay cambios)
  - `python manage.py migrate`

Pruebas
- Los tests del app `chatbot` pueden correrse con:

```powershell
python manage.py test chatbot --settings=cobramax_core.settings_test
```

Contacto
- Si quieres que adapte la integración para otro proveedor de LLM (o para usar la librería oficial `openai`), lo implemento y actualizo los tests.
