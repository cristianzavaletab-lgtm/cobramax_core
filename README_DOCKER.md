# Levantar servicios con Docker (desarrollo)

Este proyecto puede ejecutar Redis, worker de Celery y Celery Beat junto con la aplicación Django usando `docker compose`.

Requisitos locales:
- Docker Desktop (Windows) o Docker Engine y docker-compose.
- Copiar `.env.example` a `.env` y ajustar variables (SMTP, Twilio, DB, Celery broker)

Pasos rápidos:

1. Copia el ejemplo de variables y edítalas:

```powershell
copy .env.example .env
# editar .env con tu editor preferido
```

2. Levantar Redis y servicios:

```powershell
# Desde la raíz del proyecto (donde está docker-compose.yml)
# Levantar Redis, web y workers en background
docker compose up -d redis web celery_worker celery_beat

# Ver logs de celery worker
docker compose logs -f celery_worker
```

3. Verificar que Celery Beat ejecuta tareas programadas:
- Revisa logs del contenedor `celramax_celery_beat` o `cobramax_celery_beat`.
- Por ejemplo, la tarea `mark-cobranza-cycle` está programada a las 00:05 y también hay tareas periódicas para notificaciones.

Notas:
- Si trabajas en Windows y `docker` no está en PATH, instala Docker Desktop y reinicia la terminal.
- Este `docker-compose.yml` es un scaffold de desarrollo. Para producción revisa imágenes, volúmenes y credenciales.
