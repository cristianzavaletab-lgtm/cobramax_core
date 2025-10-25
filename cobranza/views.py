# cobranza/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from clientes.models import Cliente
from .models import Pago, Transaccion
from usuarios.decorators import require_roles

@login_required
@require_roles(['admin', 'oficina', 'cobrador', 'cliente'])
def lista_pagos(request):
    """Lista de pagos según el rol del usuario"""
    user = request.user
    
    if user.tipo_usuario == 'admin':
        pagos = Pago.objects.all()
    elif user.tipo_usuario == 'oficina':
        pagos = Pago.objects.all()
    elif user.tipo_usuario == 'cobrador':
        # Cobradores solo ven pagos de sus clientes
        zonas_cobrador = user.zona_set.filter(activa=True)
        clientes_cobrador = Cliente.objects.filter(zona__in=zonas_cobrador)
        pagos = Pago.objects.filter(cliente__in=clientes_cobrador)
    elif user.tipo_usuario == 'cliente':
        # Clientes solo ven sus propios pagos
        try:
            cliente = Cliente.objects.get(usuario=user)
            pagos = Pago.objects.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            pagos = Pago.objects.none()
            messages.info(request, "No tienes información de cliente registrada.")
    else:
        pagos = Pago.objects.none()
    
    # Filtros
    estado_filter = request.GET.get('estado')
    metodo_filter = request.GET.get('metodo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado_filter:
        pagos = pagos.filter(estado=estado_filter)
    if metodo_filter:
        pagos = pagos.filter(metodo_pago=metodo_filter)
    if fecha_desde:
        pagos = pagos.filter(fecha_pago__gte=fecha_desde)
    if fecha_hasta:
        pagos = pagos.filter(fecha_pago__lte=fecha_hasta)
    
  # Estadísticas
    total_pagos = pagos.count()
    total_monto = pagos.aggregate(Sum('monto'))['monto__sum'] or 0
    pagos_completados = pagos.filter(estado='completado').count()
    pagos_pendientes = total_pagos - pagos_completados  # ← Agregar esta línea
    
    context = {
        'pagos': pagos,
        'user': user,
        'total_pagos': total_pagos,
        'total_monto': total_monto,
        'pagos_completados': pagos_completados,
        'pagos_pendientes': pagos_pendientes,  # ← Agregar esta línea
        'estados': Pago.ESTADO_CHOICES,
        'metodos': Pago.METODO_PAGO_CHOICES,
    }
    return render(request, 'cobranza/lista_pagos.html', context)

@login_required
@require_roles(['admin', 'oficina', 'cobrador', 'cliente'])
def registrar_pago(request, cliente_id=None):
    """Registrar un nuevo pago"""
    cliente = None
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente')
            monto = request.POST.get('monto')
            metodo_pago = request.POST.get('metodo_pago')
            fecha_pago = request.POST.get('fecha_pago')
            observaciones = request.POST.get('observaciones', '')
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            
            # Crear el pago
            pago = Pago(
                cliente=cliente,
                monto=monto,
                metodo_pago=metodo_pago,
                fecha_pago=fecha_pago,
                observaciones=observaciones,
                registrado_por=request.user
            )
            pago.save()
            
            messages.success(request, f'Pago registrado exitosamente. Código: {pago.codigo_transaccion}')
            return redirect('detalle_pago', pago_id=pago.id)
            
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
    
    # Si es cobrador, solo puede ver sus clientes
    if request.user.tipo_usuario == 'cobrador':
        zonas_cobrador = request.user.zona_set.filter(activa=True)
        clientes = Cliente.objects.filter(zona__in=zonas_cobrador)
    else:
        clientes = Cliente.objects.all()
    
    context = {
        'cliente': cliente,
        'clientes': clientes,
        'metodos_pago': Pago.METODO_PAGO_CHOICES,
        'user': request.user
    }
    return render(request, 'cobranza/registrar_pago.html', context)

@login_required
@require_roles(['admin', 'oficina', 'cobrador', 'cliente'])
def detalle_pago(request, pago_id):
    """Detalle de un pago específico"""
    pago = get_object_or_404(Pago, id=pago_id)
    user = request.user
    
    # Verificar permisos
    if user.tipo_usuario == 'cobrador' and pago.cliente.zona.cobrador != user:
        messages.error(request, "No tienes permisos para ver este pago.")
        return redirect('lista_pagos')
    elif user.tipo_usuario == 'cliente' and pago.cliente.usuario != user:
        messages.error(request, "Solo puedes ver tus propios pagos.")
        return redirect('dashboard')
    
    context = {
        'pago': pago,
        'user': user
    }
    return render(request, 'cobranza/detalle_pago.html', context)

@login_required
@require_roles(['admin', 'oficina'])
def validar_pago(request, pago_id):
    """Validar un pago pendiente"""
    
    pago = get_object_or_404(Pago, id=pago_id)
    
    if pago.estado != 'pendiente':
        messages.error(request, "Este pago ya ha sido procesado.")
        return redirect('detalle_pago', pago_id=pago.id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'aprobar':
            pago.estado = 'completado'
            pago.validado_por = request.user
            pago.fecha_validacion = timezone.now()
            pago.save()
            
            # Actualizar deuda del cliente
            pago.cliente.deuda_actual -= pago.monto
            pago.cliente.save()
            
            messages.success(request, f"Pago {pago.codigo_transaccion} validado exitosamente.")
            
        elif accion == 'rechazar':
            pago.estado = 'rechazado'
            pago.observaciones = request.POST.get('motivo', '')
            pago.save()
            messages.warning(request, f"Pago {pago.codigo_transaccion} rechazado.")
        
        return redirect('detalle_pago', pago_id=pago.id)
    
    context = {
        'pago': pago,
        'user': request.user
    }
    return render(request, 'cobranza/validar_pago.html', context)