# clientes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm
from zonas.models import Zona
from usuarios.decorators import require_roles


@login_required
@require_roles(['admin', 'oficina'])
def lista_clientes(request):
    clientes = Cliente.objects.select_related('zona', 'usuario').order_by('-fecha_creacion')
    
    # Filtros
    busqueda = request.GET.get('busqueda')
    zona_id = request.GET.get('zona')
    estado = request.GET.get('estado')
    
    if busqueda:
        clientes = clientes.filter(
            Q(usuario__first_name__icontains=busqueda) |
            Q(usuario__last_name__icontains=busqueda) |
            Q(dni__icontains=busqueda) |
            Q(telefono_principal__icontains=busqueda)
        )
    
    if zona_id:
        clientes = clientes.filter(zona_id=zona_id)
    
    if estado:
        clientes = clientes.filter(estado=estado)
    
    zonas = Zona.objects.all()
    
    context = {
        'clientes': clientes,
        'zonas': zonas,
        'busqueda': busqueda,
        'zona_filtro': zona_id,
        'estado_filtro': estado,
    }
    
    return render(request, 'clientes/lista_clientes.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False, creado_por=request.user)
            cliente.save()
            messages.success(
                request, 
                f'Cliente {cliente.nombre_completo()} agregado exitosamente. '
                f'Usuario: {cliente.usuario.username}, Contraseña inicial: {cliente.dni}'
            )
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'titulo': 'Agregar Nuevo Cliente',
    }
    
    return render(request, 'clientes/formulario.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def editar_cliente(request, cliente_id):
    """Editar cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente {cliente.nombre_completo()} actualizado exitosamente')
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nombre_completo()}',
    }
    
    return render(request, 'clientes/formulario.html', context)


@login_required
@require_roles(['admin', 'oficina', 'cobrador', 'cliente'])
def detalle_cliente(request, cliente_id):
    """Ver detalle de un cliente"""
    cliente = get_object_or_404(
        Cliente.objects.select_related('zona', 'usuario', 'creado_por'), 
        id=cliente_id
    )
    
    # Obtener pagos del cliente (si existe el modelo Pago)
    try:
        from cobranza.models import Pago
        pagos = Pago.objects.filter(cliente=cliente).order_by('-fecha_pago')[:10]
    except:
        pagos = []
    
    context = {
        'cliente': cliente,
        'pagos': pagos,
    }
    
    return render(request, 'clientes/detalle_cliente.html', context)