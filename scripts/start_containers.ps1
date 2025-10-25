# PowerShell helper para levantar contenedores necesarios (valida que docker esté instalado)
param()

function Check-Docker {
    try {
        docker version > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

if (-not (Check-Docker)) {
    Write-Error "Docker no está disponible en este equipo. Instala Docker Desktop y vuelve a intentarlo."
    exit 1
}

# Levantar servicios básicos
Write-Host "Levantando redis, web, celery_worker y celery_beat..."
docker compose up -d redis web celery_worker celery_beat
Write-Host "Contenedores solicitados. Revisa logs con: docker compose logs -f celery_worker" 
