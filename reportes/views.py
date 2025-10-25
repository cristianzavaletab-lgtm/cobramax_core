# reportes/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from clientes.models import Cliente
from cobranza.models import Pago
from zonas.models import Zona
from django.db.models import F
from django.db.models.functions import TruncDate
from usuarios.decorators import require_roles


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def dashboard_reportes(request):
    """Dashboard principal de reportes"""
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Estadísticas generales
    total_clientes = Cliente.objects.count()
    clientes_activos = Cliente.objects.filter(estado='activo').count()
    clientes_morosos = Cliente.objects.filter(estado='moroso').count()
    
    # Estadísticas de pagos del mes
    pagos_mes = Pago.objects.filter(
        fecha_pago__gte=inicio_mes,
        estado='completado'
    )
    total_ingresos_mes = pagos_mes.aggregate(Sum('monto'))['monto__sum'] or 0
    total_pagos_mes = pagos_mes.count()
    
    # Estadísticas por zona
    zonas_stats = Zona.objects.annotate(
        total_clientes=Count('cliente'),
        clientes_morosos=Count('cliente', filter=Q(cliente__estado='moroso')),
        ingresos_mes=Sum('cliente__pago__monto', 
                        filter=Q(cliente__pago__fecha_pago__gte=inicio_mes,
                               cliente__pago__estado='completado'))
    )
    
    # Métodos de pago más usados
    metodos_pago = Pago.objects.filter(estado='completado').values(
        'metodo_pago'
    ).annotate(
        total=Count('id'),
        monto_total=Sum('monto')
    ).order_by('-monto_total')[:5]

    # Ingresos últimos 7 días (para Chart.js)
    siete_dias = timezone.now() - timedelta(days=7)
    pagos_7dias_qs = Pago.objects.filter(estado='completado', fecha_pago__gte=siete_dias)
    pagos_7dias = pagos_7dias_qs.annotate(fecha=TruncDate('fecha_pago')).values('fecha').annotate(total=Sum('monto')).order_by('fecha')
    
    context = {
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'clientes_morosos': clientes_morosos,
        'total_ingresos_mes': total_ingresos_mes,
        'total_pagos_mes': total_pagos_mes,
        'zonas_stats': zonas_stats,
        'metodos_pago': metodos_pago,
        'pagos_7dias': pagos_7dias,
    }
    
    return render(request, 'reportes/dashboard.html', context)


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def reporte_ingresos(request):
    """Reporte detallado de ingresos"""
    # Obtener filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    zona_id = request.GET.get('zona')
    metodo_pago = request.GET.get('metodo_pago')
    
    # Query base
    pagos = Pago.objects.filter(estado='completado').select_related('cliente', 'cliente__zona')
    
    # Aplicar filtros
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            pagos = pagos.filter(fecha_pago__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            pagos = pagos.filter(fecha_pago__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    if zona_id:
        pagos = pagos.filter(cliente__zona_id=zona_id)
    
    if metodo_pago:
        pagos = pagos.filter(metodo_pago=metodo_pago)
    
    # Calcular totales
    total_ingresos = pagos.aggregate(Sum('monto'))['monto__sum'] or 0
    total_pagos = pagos.count()
    promedio_pago = pagos.aggregate(Avg('monto'))['monto__avg'] or 0
    
    # Ingresos por día
    ingresos_por_dia = pagos.extra({
        'fecha': "DATE(fecha_pago)"
    }).values('fecha').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('fecha')
    
    # Ingresos por zona
    ingresos_por_zona = pagos.values(
        'cliente__zona__nombre'
    ).annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Obtener zonas para el filtro
    zonas = Zona.objects.all()
    
    context = {
        'pagos': pagos[:50],  # Limitar a 50 registros para la tabla
        'total_ingresos': total_ingresos,
        'total_pagos': total_pagos,
        'promedio_pago': promedio_pago,
        'ingresos_por_dia': list(ingresos_por_dia),
        'ingresos_por_zona': list(ingresos_por_zona),
        'zonas': zonas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'zona_filtro': zona_id,
        'metodo_filtro': metodo_pago,
    }
    
    return render(request, 'reportes/ingresos.html', context)


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def api_ingresos_por_dia(request):
    """Devuelve ingresos por día (últimos 30 días) en JSON para Chart.js"""
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    pagos = Pago.objects.filter(estado='completado', fecha_pago__gte=fecha_inicio)
    datos = pagos.annotate(fecha=TruncDate('fecha_pago')).values('fecha').annotate(total=Sum('monto')).order_by('fecha')
    return JsonResponse({'datos': [{'fecha': d['fecha'].isoformat(), 'total': float(d['total'] or 0)} for d in datos]})


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def api_clientes_por_zona(request):
    zonas = Zona.objects.annotate(total_clientes=Count('cliente')).values('nombre', 'total_clientes')
    return JsonResponse({'zonas': list(zonas)})


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def api_zonas_geo(request):
    zonas = Zona.objects.annotate(total_clientes=Count('cliente')).filter(latitud__isnull=False, longitud__isnull=False)
    datos = [
        {
            'nombre': z.nombre,
            'lat': float(z.latitud),
            'lng': float(z.longitud),
            'total_clientes': z.total_clientes
        }
        for z in zonas
    ]
    return JsonResponse({'zonas': datos})


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def api_metodos_pago(request):
    """Devuelve totales por método de pago en JSON para Chart.js"""
    datos = Pago.objects.filter(estado='completado').values('metodo_pago').annotate(total=Sum('monto')).order_by('-total')
    resultados = [
        {'metodo': d['metodo_pago'] or 'Desconocido', 'total': float(d['total'] or 0)}
        for d in datos
    ]
    return JsonResponse({'metodos': resultados})


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def reporte_morosos(request):
    """Reporte de clientes morosos"""
    # Obtener filtros
    zona_id = request.GET.get('zona')
    dias_mora = request.GET.get('dias_mora', 30)
    
    # Clientes morosos
    clientes_morosos = Cliente.objects.filter(
        estado='moroso'
    ).select_related('zona')
    
    if zona_id:
        clientes_morosos = clientes_morosos.filter(zona_id=zona_id)
    
    # Calcular deuda total (usar campo 'deuda_actual' presente en Cliente)
    deuda_total = clientes_morosos.aggregate(Sum('deuda_actual'))['deuda_actual__sum'] or 0
    total_morosos = clientes_morosos.count()
    
    # Morosos por zona
    morosos_por_zona = clientes_morosos.values(
        'zona__nombre'
    ).annotate(
    total=Count('id'),
    deuda=Sum('deuda_actual')
    ).order_by('-total')
    
    zonas = Zona.objects.all()
    
    context = {
        'clientes_morosos': clientes_morosos,
        'total_morosos': total_morosos,
        'deuda_total': deuda_total,
        'morosos_por_zona': list(morosos_por_zona),
        'zonas': zonas,
        'zona_filtro': zona_id,
        'dias_mora': dias_mora,
    }
    
    return render(request, 'reportes/morosos.html', context)


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def reporte_clientes(request):
    """Reporte general de clientes"""
    zona_id = request.GET.get('zona')
    estado = request.GET.get('estado')
    
    clientes = Cliente.objects.select_related('zona')
    
    if zona_id:
        clientes = clientes.filter(zona_id=zona_id)
    
    if estado:
        clientes = clientes.filter(estado=estado)
    
    # Estadísticas
    total_clientes = clientes.count()
    clientes_activos = clientes.filter(estado='activo').count()
    clientes_suspendidos = clientes.filter(estado='suspendido').count()
    clientes_morosos = clientes.filter(estado='moroso').count()
    
    # Clientes por zona
    clientes_por_zona = clientes.values(
        'zona__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')
    
    zonas = Zona.objects.all()
    
    context = {
        'clientes': clientes[:50],
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'clientes_suspendidos': clientes_suspendidos,
        'clientes_morosos': clientes_morosos,
        'clientes_por_zona': list(clientes_por_zona),
        'zonas': zonas,
        'zona_filtro': zona_id,
        'estado_filtro': estado,
    }
    
    return render(request, 'reportes/clientes.html', context)


@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def reporte_zonas(request):
    """Reporte de rendimiento por zonas"""
    zonas = Zona.objects.annotate(
        total_clientes=Count('cliente'),
        clientes_activos=Count('cliente', filter=Q(cliente__estado='activo')),
        clientes_morosos=Count('cliente', filter=Q(cliente__estado='moroso')),
        ingresos_mes=Sum('cliente__pago__monto', 
                        filter=Q(cliente__pago__estado='completado',
                               cliente__pago__fecha_pago__gte=timezone.now().replace(day=1)))
    )
    
    context = {
        'zonas': zonas,
    }
    
    return render(request, 'reportes/zonas.html', context)