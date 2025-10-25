# chatbot/views.py
import json
import re
import urllib.request
import urllib.error
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .models import PreguntaFrecuente, ConversacionChatbot, MensajeChatbot, TicketSoporte, HistorialTicket
from .forms import PreguntaFrecuenteForm, TicketSoporteForm, BusquedaChatbotForm
from clientes.models import Cliente
from usuarios.decorators import require_roles
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger(__name__)


# =======================
# Vistas públicas del chatbot
# =======================

@login_required
@require_roles(['cliente'])
def chatbot_interface(request):
    form = BusquedaChatbotForm()
    preguntas_populares = PreguntaFrecuente.objects.filter(activa=True).order_by('-veces_consultada')[:8]
    
    context = {
        'form': form,
        'preguntas_populares': preguntas_populares,
    }
    return render(request, 'chatbot/chatbot.html', context)


@login_required
@require_roles(['cliente'])
def buscar_respuesta(request):
    """API para buscar respuestas del chatbot"""
    if request.method == 'POST':
        form = BusquedaChatbotForm(request.POST)
        if form.is_valid():
            consulta = form.cleaned_data['consulta'].lower().strip()
            preguntas = PreguntaFrecuente.objects.filter(activa=True)
            
            # Búsqueda por palabras clave
            palabras = consulta.split()
            queries = []

            for palabra in palabras:
                queries.append(Q(pregunta__icontains=palabra))
                queries.append(Q(respuesta__icontains=palabra))
                queries.append(Q(palabras_clave__icontains=palabra))

            if queries:
                query = queries.pop()
                for item in queries:
                    query |= item
                preguntas = preguntas.filter(query)

            preguntas = preguntas.distinct().order_by('-veces_consultada')

            if preguntas.exists():
                pregunta = preguntas.first()
                pregunta.incrementar_consultas()
                
                return JsonResponse({
                    'success': True,
                    'respuesta': pregunta.respuesta,
                    'pregunta_relacionada': pregunta.pregunta,
                    'categoria': pregunta.get_categoria_display(),
                    'sugerencias': list(preguntas[1:5].values('pregunta', 'id'))
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'No encontré una respuesta específica para tu consulta. ¿Te gustaría que un agente te ayude?',
                    'sugerir_ticket': True
                })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@require_roles(['cliente'])
def iniciar_conversacion(request):
    """Iniciar una nueva conversación con el chatbot"""
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        mensaje = request.POST.get('mensaje')
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            conversacion, created = ConversacionChatbot.objects.get_or_create(
                cliente=cliente,
                estado='activa',
                defaults={'fecha_inicio': timezone.now()}
            )

            MensajeChatbot.objects.create(
                conversacion=conversacion,
                tipo='usuario',
                contenido=mensaje
            )

            respuesta = buscar_respuesta_automatica(mensaje)

            MensajeChatbot.objects.create(
                conversacion=conversacion,
                tipo='bot',
                contenido=respuesta['mensaje'],
                pregunta_relacionada=respuesta.get('pregunta')
            )

            return JsonResponse({
                'success': True,
                'conversacion_id': conversacion.id,
                'respuesta': respuesta['mensaje'],
                'sugerir_ticket': respuesta.get('sugerir_ticket', False)
            })
            
        except Cliente.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cliente no encontrado'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def buscar_respuesta_automatica(mensaje):
    """Lógica para buscar respuestas automáticas"""
    mensaje_lower = mensaje.lower()

    palabras_pagos = ['pago', 'factura', 'cuota', 'deuda', 'vencimiento', 'pagando', 'pagar']
    palabras_tecnico = ['internet', 'lento', 'caido', 'conexion', 'wifi', 'router', 'señal', 'velocidad']
    palabras_servicio = ['contrato', 'plan', 'cambio', 'suspender', 'reactivar', 'baja']
    palabras_general = ['hola', 'buenos', 'dias', 'tardes', 'noches', 'gracias', 'ayuda']

    if any(palabra in mensaje_lower for palabra in palabras_pagos):
        categoria = 'pagos'
    elif any(palabra in mensaje_lower for palabra in palabras_tecnico):
        categoria = 'tecnico'
    elif any(palabra in mensaje_lower for palabra in palabras_servicio):
        categoria = 'servicio'
    elif any(palabra in mensaje_lower for palabra in palabras_general):
        categoria = 'general'
    else:
        categoria = None

    if categoria:
        preguntas = PreguntaFrecuente.objects.filter(categoria=categoria, activa=True)
        if preguntas.exists():
            pregunta = preguntas.first()
            pregunta.incrementar_consultas()
            return {
                'mensaje': pregunta.respuesta,
                'pregunta': pregunta
            }

    return {
        'mensaje': 'Lo siento, solo puedo responder preguntas relacionadas con el proyecto COBRA-MAX. ¿Tu pregunta está relacionada con pagos, técnico, servicio, cuenta o notificaciones?',
        'sugerir_ticket': True
    }



@login_required
@require_roles(['cliente'])
def chatbot_send(request):
    """Endpoint JSON para enviar un mensaje y obtener respuesta (OpenAI si está configurado)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    # Soportar JSON o form-urlencoded
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode())
        except Exception:
            return JsonResponse({'success': False, 'error': 'JSON inválido'})
        message = payload.get('message')
    else:
        message = request.POST.get('message')

    if not message:
        return JsonResponse({'success': False, 'error': 'Mensaje vacío'})

    # Obtener cliente asociado al usuario
    try:
        cliente = Cliente.objects.get(usuario=request.user)
    except Cliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'})

    conversacion, created = ConversacionChatbot.objects.get_or_create(
        cliente=cliente,
        estado='activa',
        defaults={'fecha_inicio': timezone.now()}
    )

    # RATE LIMIT: permitir 10 mensajes por ventana de 60 segundos por usuario
    window = getattr(settings, 'CHATBOT_RATE_WINDOW', 60)  # segundos
    limit = getattr(settings, 'CHATBOT_RATE_LIMIT', 10)
    rl_key = f"chatbot_rl:{request.user.pk}"
    current = cache.get(rl_key, 0)
    if current >= limit:
        return JsonResponse({'success': False, 'error': 'Rate limit excedido. Intenta de nuevo más tarde.'}, status=429)
    # Intentar añadir la clave con valor 1 y expiración; si ya existe, incrementarla.
    added = cache.add(rl_key, 1, timeout=window)
    if not added:
        try:
            cache.incr(rl_key)
        except Exception:
            # En caso raro de carrera o backend que no soporte incr, asegurar el set
            cache.set(rl_key, cache.get(rl_key, 0) + 1, timeout=window)

    # Guardar mensaje de usuario
    MensajeChatbot.objects.create(
        conversacion=conversacion,
        tipo='usuario',
        contenido=message
    )

    respuesta_text = None
    sugerir_ticket = False

    # Si hay clave de OpenAI en settings, intentar llamar al servicio
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if api_key:
        # Intentar llamar a la API con reintentos y manejo de errores más fino
        api_url = 'https://api.openai.com/v1/chat/completions'
        system_prompt = (
            "Eres un asistente técnico especializado EXCLUSIVAMENTE en el proyecto de "
            "telecomunicaciones COBRA-MAX. Responde solo a preguntas relacionadas con este proyecto: "
            "pagos, facturación, fechas de vencimiento, cortes y reconexiones, problemas técnicos de conexión, "
            "configuración de clientes, asignación de zonas, notificaciones (email/Twilio), despliegue (Docker, Celery, Redis), "
            "integraciones y administración del sistema. Si la consulta NO está relacionada con COBRA-MAX o es temática general "
            "(recetas, política, medicina, etc.), responde exactamente: 'Lo siento, solo puedo responder preguntas relacionadas con el proyecto COBRA-MAX.' "
            "No inventes información fuera del repositorio ni supongas credenciales. Si no conoces la respuesta, di 'No sé' y sugiere crear un ticket. "
            "Responde en español de forma concisa y con pasos accionables cuando aplique."
        )

        body = {
            'model': getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': message}
            ],
            'max_tokens': 256,
            'temperature': 0.2,
        }

        req_data = json.dumps(body).encode('utf-8')
        req_headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        retry_count = getattr(settings, 'CHATBOT_RETRY_COUNT', 2)
        backoff = getattr(settings, 'CHATBOT_RETRY_BACKOFF', 1)
        last_exc = None
        for attempt in range(retry_count + 1):
            try:
                req = urllib.request.Request(api_url, data=req_data, headers=req_headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                respuesta_text = resp_data['choices'][0]['message']['content'].strip()
                break
            except urllib.error.HTTPError as e:
                # Errores HTTP (posible 429 o 5xx)
                last_exc = e
                status = getattr(e, 'code', None)
                logger.error('OpenAI HTTPError (attempt %s): %s', attempt, e)
                if status == 429:
                    # Rate limited by OpenAI
                    respuesta_text = 'Lo siento, el servicio de respuestas está temporalmente sobrecargado. Intenta de nuevo en unos segundos.'
                    sugerir_ticket = False
                    # Exponer código de error para frontend
                    return JsonResponse({'success': False, 'error': 'rate_limited', 'mensaje': respuesta_text}, status=429)
                # en 5xx intentaremos reintentar
            except Exception as e:
                last_exc = e
                logger.exception('Error llamando a OpenAI (attempt %s): %s', attempt, e)
            # Esperar antes de reintentar
            if attempt < retry_count:
                import time
                time.sleep(backoff * (attempt + 1))

        else:
            # Si todos los reintentos fallaron
            respuesta_text = 'Lo siento, hubo un error al procesar tu consulta. Puedes intentar de nuevo o solicitar atención personalizada.'
            sugerir_ticket = True
            # Registrar un log con detalle para auditoría
            logger.error('OpenAI llamadas fallaron completamente. Última excepción: %s', repr(last_exc))
            # Si está activada la creación automática de ticket al fallar, crear uno
            if getattr(settings, 'AUTO_TICKET_ON_AI_ERROR', False):
                try:
                    ticket = TicketSoporte.objects.create(
                        conversacion=conversacion,
                        titulo=f'Falló asistente AI para cliente {cliente.id}',
                        descripcion=f'Fallo al intentar usar OpenAI: {str(last_exc)}\nMensaje del usuario: {message}',
                        prioridad='media',
                        categoria='tecnico',
                        creado_por=request.user if request.user.is_authenticated else None
                    )
                    HistorialTicket.objects.create(ticket=ticket, usuario=request.user if request.user.is_authenticated else None, accion='Ticket generado por fallo AI')
                    # Informar al frontend que se creó ticket
                    return JsonResponse({'success': False, 'error': 'ai_unavailable', 'mensaje': respuesta_text, 'ticket_id': ticket.id})
                except Exception:
                    logger.exception('Error creando ticket automático tras fallo AI')
    else:
        # Fallback local: buscar en preguntas frecuentes
        resultado = buscar_respuesta_automatica(message)
        respuesta_text = resultado.get('mensaje')
        sugerir_ticket = resultado.get('sugerir_ticket', False)

    # Guardar respuesta del bot
    MensajeChatbot.objects.create(
        conversacion=conversacion,
        tipo='bot',
        contenido=respuesta_text
    )

    return JsonResponse({
        'success': True,
        'respuesta': respuesta_text,
        'sugerir_ticket': sugerir_ticket,
        'conversacion_id': conversacion.id
    })


@login_required
@require_roles(['cliente'])
@require_POST
def chatbot_create_ticket(request):
    """Crear ticket vía AJAX desde la UI del chatbot."""
    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid_json', 'mensaje': 'JSON inválido'}, status=400)

    titulo = payload.get('titulo') or 'Solicitud de soporte desde Chatbot'
    descripcion = payload.get('descripcion') or payload.get('mensaje') or ''
    categoria = payload.get('categoria') or 'tecnico'

    try:
        conversacion_id = payload.get('conversacion_id')
        conversacion_obj = ConversacionChatbot.objects.get(id=conversacion_id) if conversacion_id else None
    except ConversacionChatbot.DoesNotExist:
        conversacion_obj = None

    try:
        ticket = TicketSoporte.objects.create(
            conversacion=conversacion_obj,
            titulo=titulo,
            descripcion=descripcion,
            prioridad=payload.get('prioridad', 'media'),
            categoria=categoria,
            creado_por=request.user
        )
        HistorialTicket.objects.create(ticket=ticket, usuario=request.user, accion='Ticket creado desde Chatbot UI')
        return JsonResponse({'success': True, 'ticket_id': ticket.id, 'mensaje': 'Ticket creado, un agente te contactará.'})
    except Exception as e:
        logger.exception('Error creando ticket desde chatbot_create_ticket: %s', e)
        return JsonResponse({'success': False, 'error': 'ticket_error', 'mensaje': 'No se pudo crear el ticket. Intenta de nuevo.'}, status=500)


@login_required
@require_roles(['cliente'])
def chatbot_history(request, conversacion_id):
    """Devolver historial de mensajes para una conversación (JSON)."""
    try:
        conv = ConversacionChatbot.objects.get(id=conversacion_id, cliente__usuario=request.user)
    except ConversacionChatbot.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversación no encontrada'}, status=404)

    mensajes = conv.mensajes.order_by('timestamp').values('tipo', 'contenido', 'timestamp')
    # serializar timestamps a ISO
    data = [
        {'tipo': m['tipo'], 'contenido': m['contenido'], 'timestamp': m['timestamp'].isoformat() if m['timestamp'] else None}
        for m in mensajes
    ]
    return JsonResponse({'success': True, 'mensajes': data})


# =======================
# Vistas de administración
# =======================

@login_required
@require_roles(['admin', 'oficina'])
def gestion_preguntas_frecuentes(request):
    """Gestión de preguntas frecuentes"""
    preguntas = PreguntaFrecuente.objects.all().order_by('categoria', '-veces_consultada')

    # Calcular estadísticas
    total_preguntas = preguntas.count()
    preguntas_activas = preguntas.filter(activa=True).count()
    total_consultas = preguntas.aggregate(total=Sum('veces_consultada'))['total'] or 0

    context = {
        'preguntas': preguntas,
        'categorias': PreguntaFrecuente.CATEGORIA_CHOICES,
        'total_preguntas': total_preguntas,
        'preguntas_activas': preguntas_activas,
        'total_consultas': total_consultas,
    }
    return render(request, 'chatbot/gestion_preguntas.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def agregar_pregunta_frecuente(request):
    """Agregar nueva pregunta frecuente"""
    if request.method == 'POST':
        form = PreguntaFrecuenteForm(request.POST)
        if form.is_valid():
            pregunta = form.save(commit=False)
            pregunta.creada_por = request.user
            pregunta.save()
            messages.success(request, 'Pregunta frecuente agregada exitosamente')
            return redirect('gestion_preguntas_frecuentes')
    else:
        form = PreguntaFrecuenteForm()
    
    return render(request, 'chatbot/agregar_pregunta.html', {'form': form})


@login_required
@require_roles(['admin', 'oficina'])
def editar_pregunta_frecuente(request, pregunta_id):
    """Editar pregunta frecuente existente"""
    pregunta = get_object_or_404(PreguntaFrecuente, id=pregunta_id)
    
    if request.method == 'POST':
        form = PreguntaFrecuenteForm(request.POST, instance=pregunta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pregunta frecuente actualizada exitosamente')
            return redirect('gestion_preguntas_frecuentes')
    else:
        form = PreguntaFrecuenteForm(instance=pregunta)
    
    return render(request, 'chatbot/editar_pregunta.html', {'form': form, 'pregunta': pregunta})


@login_required
@require_roles(['admin', 'oficina'])
def toggle_pregunta_frecuente(request, pregunta_id):
    """Activar/desactivar pregunta frecuente"""
    pregunta = get_object_or_404(PreguntaFrecuente, id=pregunta_id)
    pregunta.activa = not pregunta.activa
    pregunta.save()
    
    estado = "activada" if pregunta.activa else "desactivada"
    messages.success(request, f'Pregunta {estado} exitosamente')
    return redirect('gestion_preguntas_frecuentes')


@login_required
@require_roles(['admin', 'oficina'])
def dashboard_tickets(request):
    """Dashboard de tickets de soporte"""
    tickets = TicketSoporte.objects.all().select_related('agente_asignado', 'creado_por')
    
    total_tickets = tickets.count()
    tickets_abiertos = tickets.filter(estado='abierto').count()
    tickets_en_progreso = tickets.filter(estado='en_progreso').count()
    tickets_resueltos = tickets.filter(estado='resuelto').count()
    
    context = {
        'tickets': tickets,
        'total_tickets': total_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_en_progreso': tickets_en_progreso,
        'tickets_resueltos': tickets_resueltos,
    }
    return render(request, 'chatbot/dashboard_tickets.html', context)


@login_required
@require_roles(['admin', 'oficina'])
def crear_ticket_manual(request):
    """Crear ticket de soporte manualmente"""
    if request.method == 'POST':
        form = TicketSoporteForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.creado_por = request.user
            ticket.save()
            
            HistorialTicket.objects.create(
                ticket=ticket,
                usuario=request.user,
                accion='Ticket creado manualmente'
            )
            
            messages.success(request, 'Ticket creado exitosamente')
            return redirect('dashboard_tickets')
    else:
        form = TicketSoporteForm()
    
    return render(request, 'chatbot/crear_ticket.html', {'form': form})
