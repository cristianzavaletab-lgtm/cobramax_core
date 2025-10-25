# notificaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Notificacion, PlantillaNotificacion, RegistroEnvio
from .forms import NotificacionForm, PlantillaNotificacionForm, NotificacionMasivaForm
from clientes.models import Cliente
from zonas.models import Zona
from .services import NotificacionService
from .tasks import enviar_mensaje_directo
from django import forms
from types import SimpleNamespace
import json
from django.views.decorators.http import require_GET
import logging
from usuarios.decorators import require_roles
from django.db import models


# =======================
# Dashboard y Listas
# =======================

@login_required
@require_roles(['admin', 'oficina'])
def dashboard_notificaciones(request):
    """Dashboard principal de notificaciones"""
    # Filtros temporales
    hoy = timezone.now()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)

    # Estadísticas generales
    total_notificaciones = Notificacion.objects.count()
    notificaciones_pendientes = Notificacion.objects.filter(estado='pendiente').count()
    notificaciones_enviadas = Notificacion.objects.filter(estado='enviado').count()
    notificaciones_fallidas = Notificacion.objects.filter(estado='fallido').count()

    # Notificaciones recientes (últimas 10)
    notificaciones_recientes = Notificacion.objects.select_related(
        'cliente', 'zona', 'enviado_por'
    ).order_by('-fecha_creacion')[:10]

    # Notificaciones por tipo (últimos 30 días)
    notificaciones_por_tipo = Notificacion.objects.filter(
        fecha_creacion__gte=hace_30_dias
    ).values('tipo').annotate(total=Count('id'))

    # Tasa de éxito (últimos 7 días)
    envios_7_dias = Notificacion.objects.filter(fecha_creacion__gte=hace_7_dias)
    total_enviadas = envios_7_dias.filter(estado='enviado').count()
    total_intentos = envios_7_dias.count()
    tasa_exito = (total_enviadas / total_intentos * 100) if total_intentos > 0 else 0

    context = {
        'total_notificaciones': total_notificaciones,
        'notificaciones_pendientes': notificaciones_pendientes,
        'notificaciones_enviadas': notificaciones_enviadas,
        'notificaciones_fallidas': notificaciones_fallidas,
        'notificaciones_recientes': notificaciones_recientes,
        'notificaciones_por_tipo': list(notificaciones_por_tipo),
        'tasa_exito': round(tasa_exito, 2),
    }

    return render(request, 'notificaciones/dashboard.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def lista_notificaciones(request):
    """Lista completa de notificaciones con filtros"""
    notificaciones = Notificacion.objects.select_related(
        'cliente', 'zona', 'enviado_por'
    ).order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    zona_id = request.GET.get('zona')
    
    if estado:
        notificaciones = notificaciones.filter(estado=estado)
    if tipo:
        notificaciones = notificaciones.filter(tipo=tipo)
    if zona_id:
        notificaciones = notificaciones.filter(zona_id=zona_id)
    
    zonas = Zona.objects.all()
    
    context = {
        'notificaciones': notificaciones,
        'zonas': zonas,
        'estado_filtro': estado,
        'tipo_filtro': tipo,
        'zona_filtro': zona_id,
    }
    
    return render(request, 'notificaciones/lista.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def detalle_notificacion(request, notificacion_id):
    """Ver detalle de una notificación"""
    notificacion = get_object_or_404(
        Notificacion.objects.select_related('cliente', 'zona', 'enviado_por'),
        id=notificacion_id
    )
    
    # Obtener registros de envío
    registros_envio = RegistroEnvio.objects.filter(
        notificacion=notificacion
    ).order_by('-fecha_intento')
    
    context = {
        'notificacion': notificacion,
        'registros_envio': registros_envio,
    }
    
    return render(request, 'notificaciones/detalle.html', context)


# =======================
# Crear y Enviar Notificaciones
# =======================

@login_required
@require_roles(['admin', 'oficina', 'cobrador'])
def crear_notificacion(request):
    """Crear notificación individual"""
    if request.method == 'POST':
        form = NotificacionForm(request.POST)
        if form.is_valid():
            notificacion = form.save(commit=False)
            notificacion.enviado_por = request.user
            notificacion.save()
            
            # Intentar enviar inmediatamente
            if notificacion.enviar_notificacion():
                messages.success(request, 'Notificación enviada exitosamente')
            else:
                messages.warning(request, 'Notificación creada pero el envío falló')
            
            return redirect('dashboard_notificaciones')
    else:
        form = NotificacionForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Notificación Individual',
    }
    
    return render(request, 'notificaciones/crear.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def reenviar_notificacion(request, notificacion_id):
    """Reenviar una notificación fallida"""
    notificacion = get_object_or_404(Notificacion, id=notificacion_id)
    
    if notificacion.estado == 'enviado':
        messages.warning(request, 'Esta notificación ya fue enviada exitosamente')
    else:
        if notificacion.enviar_notificacion():
            messages.success(request, 'Notificación reenviada exitosamente')
        else:
            messages.error(request, 'No se pudo reenviar la notificación')
    
    return redirect('detalle_notificacion', notificacion_id=notificacion.id)


@login_required
@require_roles(['admin', 'oficina'])
def notificacion_masiva(request):
    """Enviar notificaciones masivas"""
    if request.method == 'POST':
        form = NotificacionMasivaForm(request.POST)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            mensaje = form.cleaned_data['mensaje']
            zona = form.cleaned_data.get('zona')
            estado_cliente = form.cleaned_data.get('estado_cliente')
            usar_plantilla = form.cleaned_data.get('usar_plantilla')
            plantilla = form.cleaned_data.get('plantilla')
            
            # Filtrar clientes
            clientes = Cliente.objects.filter(estado='activo')
            
            if zona:
                clientes = clientes.filter(zona=zona)
            
            if estado_cliente:
                clientes = clientes.filter(estado=estado_cliente)
            
            # Usar plantilla si fue seleccionada
            if usar_plantilla and plantilla:
                mensaje = plantilla.contenido
            
            # Crear notificaciones
            contador_exitosas = 0
            contador_fallidas = 0
            
            for cliente in clientes:
                notificacion = Notificacion.objects.create(
                    cliente=cliente,
                    zona=cliente.zona,
                    tipo=tipo,
                    mensaje=mensaje,
                    canal='whatsapp',  # Por defecto
                    enviado_por=request.user
                )
                
                if notificacion.enviar_notificacion():
                    contador_exitosas += 1
                else:
                    contador_fallidas += 1
            
            messages.success(
                request, 
                f'Notificaciones masivas enviadas: {contador_exitosas} exitosas, {contador_fallidas} fallidas'
            )
            return redirect('dashboard_notificaciones')
    else:
        form = NotificacionMasivaForm()
    
    context = {
        'form': form,
        'titulo': 'Enviar Notificaciones Masivas',
    }
    
    return render(request, 'notificaciones/masiva.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def test_send_notification(request):
    """Página simple para probar envío de WhatsApp / Email (solo desarrollo)."""
    class TestForm(forms.Form):
        canal = forms.ChoiceField(choices=(('whatsapp','WhatsApp'),('email','Email')), required=True)
        telefono = forms.CharField(required=False)
        email = forms.EmailField(required=False)
        mensaje = forms.CharField(widget=forms.Textarea, required=True)

    logger = logging.getLogger(__name__)
    result = None
    if request.method == 'POST':
        form = TestForm(request.POST)
        # set widget attrs for bootstrap styling
        for fname, attrs in {
            'canal': {'class': 'form-select form-select-sm'},
            'telefono': {'class': 'form-control form-control-sm', 'placeholder': '+51987654321'},
            'email': {'class': 'form-control form-control-sm', 'placeholder': 'ejemplo@correo.com'},
            'mensaje': {'class': 'form-control form-control-sm', 'rows': '4', 'placeholder': 'Mensaje de prueba'},
        }.items():
            if fname in form.fields:
                form.fields[fname].widget.attrs.update(attrs)

        if form.is_valid():
            canal = form.cleaned_data['canal']
            telefono = form.cleaned_data.get('telefono')
            email = form.cleaned_data.get('email')
            mensaje = form.cleaned_data['mensaje']

            svc = NotificacionService()
            # Crear un objeto temporal tipo Notificacion simulado si es necesario
            DummyCliente = SimpleNamespace(
                nombre=request.user.get_full_name() or request.user.username,
                telefono_principal=telefono or '',
                email=email or '',
                nombre_completo=request.user.get_full_name() or request.user.username,
                zona=getattr(request.user, 'zona', None) or None,
            )

            # Para tests rápidos: por defecto encolamos la tarea en Celery
            enqueue = request.POST.get('enqueue', '1') in ['1', 'true', 'on', 'yes']

            if enqueue:
                # Intentamos encolar la tarea asíncrona; si falla (p.ej. broker no disponible)
                # hacemos fallback a envío síncrono y retornamos un resultado claro.
                try:
                    task = enviar_mensaje_directo.delay(canal, telefono or None, email or None, mensaje, getattr(request.user, 'id', None))
                    payload = {'queued': True, 'task_id': getattr(task, 'id', None)}
                    return JsonResponse({'ok': True, 'result': payload})
                except Exception as e:
                    # Registrar el error y realizar envío síncrono como fallback
                    logger.exception('Error encolar tarea Celery - realizando envío síncrono: %s', e)
                    # Envío síncrono (mismo comportamiento que cuando enqueue==False)
                    if canal == 'whatsapp':
                        result = svc.whatsapp_service.enviar_mensaje(telefono, mensaje)
                    else:
                        result = svc.email_service.enviar_email(email, 'Prueba Cobramax', mensaje, html_message=None)

                    # Normalizar resultado a un dict simple y anotar que no fue encolado
                    if isinstance(result, dict):
                        payload = result
                    else:
                        payload = {'success': bool(result), 'detail': str(result)}
                    payload.update({'queued': False, 'error': str(e)})

                    # Intentar persistir la notificación y registro si encontramos un Cliente
                    stored = False
                    try:
                        cliente_obj = None
                        if telefono:
                            cliente_obj = Cliente.objects.filter(telefono__icontains=telefono).first()
                        if not cliente_obj and email:
                            cliente_obj = Cliente.objects.filter(email__iexact=email).first()

                        if cliente_obj:
                            noti = Notificacion.objects.create(
                                cliente=cliente_obj,
                                zona=getattr(cliente_obj, 'zona', None),
                                tipo='general',
                                mensaje=mensaje,
                                canal=canal,
                                enviado_por=request.user
                            )
                            # Ajustar metadatos según resultado
                            if payload.get('success'):
                                noti.estado = 'enviado'
                                noti.fecha_envio = timezone.now()
                            else:
                                noti.estado = 'fallido'
                                noti.error_mensaje = payload.get('detail') or payload.get('error')
                            noti.destinatario_telefono = telefono or None
                            noti.destinatario_email = email or None
                            noti.save()

                            RegistroEnvio.objects.create(
                                notificacion=noti,
                                exitoso=bool(payload.get('success')),
                                mensaje_error=noti.error_mensaje,
                                respuesta_api=json.dumps(payload, default=str)
                            )
                            stored = True
                    except Exception:
                        logger.exception('No se pudo persistir registro de envío en fallback síncrono')

                    payload.update({'stored': stored})
                    return JsonResponse({'ok': True, 'result': payload})
            else:
                # Envío síncrono - útil para debugging
                if canal == 'whatsapp':
                    result = svc.whatsapp_service.enviar_mensaje(telefono, mensaje)
                else:
                    result = svc.email_service.enviar_email(email, 'Prueba Cobramax', mensaje, html_message=None)

                # Normalizar resultado a un dict simple
                if isinstance(result, dict):
                    payload = result
                else:
                    payload = {'success': bool(result), 'detail': str(result)}

                # Intentar persistir la notificación y registro si encontramos un Cliente
                stored = False
                try:
                    cliente_obj = None
                    if telefono:
                        cliente_obj = Cliente.objects.filter(telefono__icontains=telefono).first()
                    if not cliente_obj and email:
                        cliente_obj = Cliente.objects.filter(email__iexact=email).first()

                    if cliente_obj:
                        noti = Notificacion.objects.create(
                            cliente=cliente_obj,
                            zona=getattr(cliente_obj, 'zona', None),
                            tipo='general',
                            mensaje=mensaje,
                            canal=canal,
                            enviado_por=request.user
                        )
                        # Ajustar metadatos según resultado
                        if payload.get('success'):
                            noti.estado = 'enviado'
                            noti.fecha_envio = timezone.now()
                        else:
                            noti.estado = 'fallido'
                            noti.error_mensaje = payload.get('detail') or payload.get('error')
                        noti.destinatario_telefono = telefono or None
                        noti.destinatario_email = email or None
                        noti.save()

                        RegistroEnvio.objects.create(
                            notificacion=noti,
                            exitoso=bool(payload.get('success')),
                            mensaje_error=noti.error_mensaje,
                            respuesta_api=json.dumps(payload, default=str)
                        )
                        stored = True
                except Exception:
                    logger.exception('No se pudo persistir registro de envío en envío síncrono')

                payload.update({'stored': stored})
                return JsonResponse({'ok': True, 'result': payload})
        # Si llegamos aquí, es porque request.method == 'POST' pero no hubo redirección
        # Si el formulario quedó inválido y es una petición AJAX, retornar errores
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            ('application/json' in request.META.get('HTTP_ACCEPT', ''))
        )
        if is_ajax and not form.is_valid():
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    else:
        form = TestForm()
        # set widget attrs for bootstrap styling on GET
        for fname, attrs in {
            'canal': {'class': 'form-select form-select-sm'},
            'telefono': {'class': 'form-control form-control-sm', 'placeholder': '+51987654321'},
            'email': {'class': 'form-control form-control-sm', 'placeholder': 'ejemplo@correo.com'},
            'mensaje': {'class': 'form-control form-control-sm', 'rows': '4', 'placeholder': 'Mensaje de prueba'},
        }.items():
            if fname in form.fields:
                form.fields[fname].widget.attrs.update(attrs)

    return render(request, 'notificaciones/test_send.html', {'form': form, 'result': result})


# =======================
# Gestión de Plantillas
# =======================

@login_required
@require_roles(['admin', 'oficina'])
def lista_plantillas(request):
    """Lista de plantillas de notificaciones"""
    plantillas = PlantillaNotificacion.objects.annotate(
        veces_usada=Count('notificacion')
    ).order_by('tipo', '-activa')
    
    context = {
        'plantillas': plantillas,
    }
    
    return render(request, 'notificaciones/plantillas/lista.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def crear_plantilla(request):
    """Crear nueva plantilla"""
    if request.method == 'POST':
        form = PlantillaNotificacionForm(request.POST)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.creada_por = request.user
            plantilla.save()
            messages.success(request, 'Plantilla creada exitosamente')
            return redirect('lista_plantillas')
    else:
        form = PlantillaNotificacionForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Plantilla',
    }
    
    return render(request, 'notificaciones/plantillas/crear.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def editar_plantilla(request, plantilla_id):
    """Editar plantilla existente"""
    plantilla = get_object_or_404(PlantillaNotificacion, id=plantilla_id)
    
    if request.method == 'POST':
        form = PlantillaNotificacionForm(request.POST, instance=plantilla)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plantilla actualizada exitosamente')
            return redirect('lista_plantillas')
    else:
        form = PlantillaNotificacionForm(instance=plantilla)
    
    context = {
        'form': form,
        'plantilla': plantilla,
        'titulo': 'Editar Plantilla',
    }
    
    return render(request, 'notificaciones/plantillas/editar.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def toggle_plantilla(request, plantilla_id):
    """Activar/desactivar plantilla"""
    plantilla = get_object_or_404(PlantillaNotificacion, id=plantilla_id)
    plantilla.activa = not plantilla.activa
    plantilla.save()
    
    estado = "activada" if plantilla.activa else "desactivada"
    messages.success(request, f'Plantilla {estado} exitosamente')
    
    return redirect('lista_plantillas')


# =======================
# API Endpoints
# =======================

@login_required
def obtener_plantillas_por_tipo(request):
    """API para obtener plantillas filtradas por tipo"""
    tipo = request.GET.get('tipo')
    
    plantillas = PlantillaNotificacion.objects.filter(activa=True)
    
    if tipo:
        plantillas = plantillas.filter(tipo=tipo)
    
    data = {
        'plantillas': [
            {
                'id': p.id,
                'nombre': p.nombre,
                'contenido': p.contenido,
                'tipo': p.tipo,
            }
            for p in plantillas
        ]
    }
    
    return JsonResponse(data)


@login_required
def estadisticas_notificaciones(request):
    """API para estadísticas de notificaciones"""
    dias = int(request.GET.get('dias', 30))
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    notificaciones = Notificacion.objects.filter(fecha_creacion__gte=fecha_inicio)
    
    # Por estado
    por_estado = notificaciones.values('estado').annotate(total=Count('id'))
    
    # Por tipo
    por_tipo = notificaciones.values('tipo').annotate(total=Count('id'))
    
    # Por canal
    por_canal = notificaciones.values('canal').annotate(total=Count('id'))
    
    # Por día
    por_dia = notificaciones.extra({
        'fecha': "DATE(fecha_creacion)"
    }).values('fecha').annotate(total=Count('id')).order_by('fecha')
    
    data = {
        'por_estado': list(por_estado),
        'por_tipo': list(por_tipo),
        'por_canal': list(por_canal),
        'por_dia': list(por_dia),
        'total': notificaciones.count(),
    }
    
    return JsonResponse(data)


@login_required
@require_GET
def obtener_clientes_autocomplete(request):
    """Endpoint simple para autocompletar clientes por nombre, telefono o email."""
    q = request.GET.get('q', '').strip()
    items = []
    if q:
        qs = Cliente.objects.filter(
            models.Q(nombre__icontains=q) |
            models.Q(nombre_completo__icontains=q) |
            models.Q(telefono__icontains=q) |
            models.Q(email__icontains=q)
        ).order_by('nombre')[:10]

        for c in qs:
            label = f"{c.nombre_completo or c.nombre} — {c.telefono or ''} {('<' + c.email + '>') if c.email else ''}"
            items.append({
                'id': c.id,
                'label': label,
                'nombre': c.nombre_completo or c.nombre,
                'telefono': c.telefono,
                'email': c.email,
            })

    return JsonResponse({'results': items})