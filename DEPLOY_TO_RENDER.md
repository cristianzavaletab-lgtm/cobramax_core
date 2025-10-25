# Despliegue en Render

Este documento recoge los pasos mínimos para desplegar la aplicación en Render usando la base de datos PostgreSQL gestionada y las variables de entorno.

## Variables de entorno necesarias
Añade estas variables en el Dashboard → tu servicio → Environment → Add Environment Variable

- DJANGO_SECRET_KEY = <tu clave secreta segura>
- DJANGO_DEBUG = False
- DATABASE_URL = postgresql://<usuario>:<contraseña>@<host>:<puerto>/<dbname>

Render proporciona dos tipos de endpoints para su PostgreSQL:

- URL interna (para que los servicios desplegados en Render se conecten entre sí sin exponer la base a Internet):

  postgresql://cobramax_db_user:O3QiI9mSUFVqrVB7VmpvQvqUWlCfSk3z@dpg-d3uedu9r0fns73f54k1g-a/cobramax_db

  Variable recomendada en Render (Environment): `RENDER_INTERNAL_DATABASE_URL`

- URL externa (para conectarte desde tu PC o clientes externos):

  postgresql://cobramax_db_user:O3QiI9mSUFVqrVB7VmpvQvqUWlCfSk3z@dpg-d3uedu9r0fns73f54k1g-a.oregon-postgres.render.com/cobramax_db

  Variable recomendada en Render (Environment) si necesitas que herramientas externas usen la URL: `DATABASE_URL`

Opcionales (según uso):
- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT (si prefieres usar variables separadas en lugar de DATABASE_URL)
- DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
- CELERY_BROKER_URL, CELERY_RESULT_BACKEND


## Comandos de Build / Start / Release recomendados
- Build Command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

- Start Command:

```bash
gunicorn cobramax_core.wsgi:application --bind 0.0.0.0:$PORT
```

- Release Command (opcional, se ejecuta después de cada despliegue; útil para migraciones automáticas):

```bash
python manage.py migrate
```


## Notas de seguridad y configuración
- `DJANGO_DEBUG` debe ser `False` en producción.
- `ALLOWED_HOSTS` en `cobramax_core/settings.py` ya incluye `cobramax-core.onrender.com`. Asegúrate de que el dominio coincide con el nombre de tu servicio en Render.
- Habilité `WhiteNoise` en `settings.py` para servir archivos estáticos en producción. `STATIC_ROOT` está configurado en el proyecto y `collectstatic` se debe ejecutar en el Build.
- Considera habilitar estas opciones en producción para mayor seguridad:
  - `SECURE_SSL_REDIRECT = True`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS = 31536000`


## Migraciones
Si la base de datos de Render está accesible desde el contenedor/entorno de Render, lo ideal es usar el Release Command para ejecutar las migraciones automáticamente. Alternativamente, puedes conectarte desde local (si el host es accesible) y ejecutar:

```powershell
# establecer variables de entorno temporalmente en PowerShell (ejemplo)
$env:DATABASE_URL='postgresql://cobramax_db_user:O3QiI9mSUFVqrVB7VmpvQvqUWlCfSk3z@dpg-d3uedu9r0fns73f54k1g-a.oregon-postgres.render.com:5432/cobramax_db'
& .\venv_cobramax\Scripts\python.exe manage.py migrate
```


## Troubleshooting
- Si `collectstatic` falla por `ManifestStaticFilesStorage`, ejecuta `python manage.py collectstatic --noinput` localmente para detectar archivos faltantes o referencias rotas.
- Si hay errores de conexión a la DB desde local, verifica reglas de firewall y que Render permita conexiones desde tu IP (generalmente Render DBs bloquean conexiones externas; en ese caso ejecutar migraciones en Release Command es la opción correcta).

### Conectarse desde la terminal (psql)

Comando para conectarte desde tu PC (PowerShell / Linux / macOS):

```bash
PGPASSWORD=O3QiI9mSUFVqrVB7VmpvQvqUWlCfSk3z psql -h dpg-d3uedu9r0fns73f54k1g-a.oregon-postgres.render.com -U cobramax_db_user cobramax_db
```

Parámetros:
- `-h`: Hostname externo (por ejemplo `dpg-d3uedu9r0fns73f54k1g-a.oregon-postgres.render.com`)
- `-U`: Usuario (`cobramax_db_user`)
- `cobramax_db`: Nombre de la base
- `PGPASSWORD`: contraseña (se puede usar para evitar el prompt interactivo)

Si tu red no permite conexiones externas a la DB de Render, ejecuta migraciones como Release Command en Render.


---
Generado automáticamente por el asistente de despliegue. Ajusta valores y seguridad según sea necesario.
