# zonas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Zona
from usuarios.decorators import require_roles
from .models import Departamento, Provincia, Distrito, Caserio


def api_departamentos(request):
    """API pública: lista de departamentos"""
    deps = Departamento.objects.all().order_by('nombre').values('id', 'nombre')
    return JsonResponse(list(deps), safe=False)


def api_provincias(request, departamento_id):
    provs = Provincia.objects.filter(departamento_id=departamento_id).order_by('nombre').values('id', 'nombre')
    return JsonResponse(list(provs), safe=False)


def api_distritos(request, provincia_id):
    dists = Distrito.objects.filter(provincia_id=provincia_id).order_by('nombre').values('id', 'nombre')
    return JsonResponse(list(dists), safe=False)


def api_caserios(request, distrito_id):
    cas = Caserio.objects.filter(distrito_id=distrito_id, activa=True).order_by('nombre').values('id', 'nombre')
    return JsonResponse(list(cas), safe=False)

@login_required
@require_roles(['admin', 'oficina'])
def lista_zonas(request):
    """Lista todas las zonas (solo para admin y oficina)"""
    zonas = Zona.objects.all()
    context = {
        'zonas': zonas,
        'user': request.user
    }
    return render(request, 'zonas/lista_zonas.html', context)

@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def detalle_zona(request, zona_id):
    """Detalle de una zona específica"""
    zona = get_object_or_404(Zona, id=zona_id)
    
    # Permisos: admin, oficina o cobrador asignado a la zona
    # Si es cobrador hay una comprobación extra por objeto
    if request.user.tipo_usuario == 'cobrador' and zona.cobrador != request.user:
        messages.error(request, "No tienes permisos para ver esta zona")
        return redirect('dashboard')
    
    context = {
        'zona': zona,
        'user': request.user
    }
    return render(request, 'zonas/detalle_zona.html', context)

@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def mapa_zonas(request):
    """Mapa interactivo de todas las zonas"""
    zonas = Zona.objects.filter(activa=True)

    # Si es cobrador, solo ver sus zonas
    if request.user.tipo_usuario == 'cobrador':
        zonas = zonas.filter(cobrador=request.user)

    context = {
        'zonas': zonas,
        'user': request.user
    }
    return render(request, 'zonas/mapa_zonas.html', context)