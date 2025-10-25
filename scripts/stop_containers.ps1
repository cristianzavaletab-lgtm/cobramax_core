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
    Write-Error "Docker no está disponible en este equipo."
    exit 1
}

Write-Host "Deteniendo contenedores..."
docker compose stop celery_beat celery_worker web redis
Write-Host "Contenedores detenidos. Para eliminarlos: docker compose down"
