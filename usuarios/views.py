from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import LoginForm, RegistroClienteForm, RegistroCobradorForm
from clientes.models import Cliente
from zonas.models import Zona
from .models import ActionLog
from django.core.mail import send_mail
from django.conf import settings
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()
from .decorators import require_roles

def login_view(request):
    """Vista para iniciar sesión"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'usuarios/login.html')  # ← Ahora en usuarios/login.html

@login_required
def dashboard(request):
    """Vista del dashboard principal"""
    context = {
        'total_clientes': 150,
        'ingresos_mes': 12500.00,
        'notificaciones_pendientes': 3,
    }
    return render(request, 'dashboard.html', context)  # ← En templates/dashboard.html

def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('login')


def unified_auth(request):
    """Vista unificada: login y registro (cliente/cobrador)."""
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    login_form = LoginForm(request=request)
    reg_cliente_form = RegistroClienteForm()
    reg_cobrador_form = RegistroCobradorForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            login_form = LoginForm(request=request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Credenciales inválidas')

        elif action == 'registrar_cliente':
            reg_cliente_form = RegistroClienteForm(request.POST)
            if reg_cliente_form.is_valid():
                data = reg_cliente_form.cleaned_data
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data.get('email') or '',
                    first_name=data.get('first_name') or '',
                    last_name=data.get('last_name') or '',
                )
                user.tipo_usuario = 'cliente'
                user.is_active = True
                user.save()

                # Crear registro Cliente asociado (mínimo)
                cliente_kwargs = dict(
                    usuario=user,
                    nombre=data.get('first_name') or '',
                    apellido=data.get('last_name') or '',
                    dni=data.get('dni') or '',
                    telefono_principal=data.get('telefono') or '',
                    direccion=data.get('direccion') or '',
                    zona=data.get('zona'),
                    # fecha_instalacion es obligatoria en la tabla; usar fecha actual si no se proporciona
                    fecha_instalacion=timezone.localdate(),
                    email=data.get('email') or '',
                )
                # Si el formulario proporcionó caserio, guardarlo en el cliente (campo opcional)
                if data.get('caserio'):
                    cliente_kwargs['caserio'] = data.get('caserio')

                Cliente.objects.create(**cliente_kwargs)

                # Mensaje y flujo: por defecto redirigimos a login. Si la configuración
                # AUTO_LOGIN_AFTER_REGISTER está activada, iniciamos sesión automáticamente.
                if getattr(settings, 'AUTO_LOGIN_AFTER_REGISTER', False):
                    try:
                        login(request, user)
                        messages.success(request, 'Registro exitoso. Has iniciado sesión automáticamente.')
                        return redirect('dashboard')
                    except Exception:
                        # Si algo falla en el login automático, caeremos a la ruta por defecto
                        logger.exception('Error haciendo auto-login tras registro de cliente')

                messages.success(request, 'Registro de cliente exitoso. Ya puedes iniciar sesión.')
                return redirect('login')
            else:
                messages.error(request, 'Errores en el formulario de registro de cliente')

        elif action == 'registrar_cobrador':
            reg_cobrador_form = RegistroCobradorForm(request.POST)
            if reg_cobrador_form.is_valid():
                data = reg_cobrador_form.cleaned_data
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data.get('email') or '',
                    first_name=data.get('first_name') or '',
                    last_name=data.get('last_name') or '',
                )
                # Marcar cobrador como pendiente (no activo hasta aprobación)
                user.tipo_usuario = 'cobrador'
                user.is_active = False
                user.save()

                # Asignar cobrador a la zona (si existe)
                zona = data.get('zona')
                if zona:
                    try:
                        zona.cobrador = user
                        zona.save()
                    except Exception:
                        # silent: Si no se puede asignar, se deja pendiente
                        pass

                messages.success(request, 'Registro de cobrador recibido. Espera aprobación de Oficina o Administrador.')
                return redirect('login')
            else:
                messages.error(request, 'Errores en el formulario de registro de cobrador')

    return render(request, 'auth/login_register.html', {
        'login_form': login_form,
        'reg_cliente_form': reg_cliente_form,
        'reg_cobrador_form': reg_cobrador_form,
    })


@login_required
def pending_cobradores(request):
    """Lista cobradores pendientes de aprobación (solo Oficina/Admin)."""
    # Permisos: solo admin u oficina (el decorador arriba se encargará)
    pendientes = User.objects.filter(tipo_usuario='cobrador', is_active=False)
    return render(request, 'usuarios/pending_cobradores.html', {'pendientes': pendientes})


@login_required
@require_roles(['admin', 'oficina'])
def approve_cobrador(request, user_id):

    try:
        u = User.objects.get(pk=user_id, tipo_usuario='cobrador')
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('pending_cobradores')

    if request.method == 'POST':
        u.is_active = True
        u.save()
        # Registrar auditoría
        try:
            ActionLog.objects.create(
                actor=request.user,
                target_user=u,
                action='approve_cobrador',
                detail=f'Cobrador aprobado por {request.user.username}'
            )
        except Exception:
            logger.exception('Error registrando ActionLog al aprobar cobrador')

        # Notificar por email (si está configurado)
        if u.email:
            try:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
                subject = 'Cuenta aprobada - COBRA-MAX'
                message = f"Hola {u.get_full_name() or u.username},\n\nTu cuenta de cobrador ha sido aprobada. Ya puedes iniciar sesión en el sistema.\n\nSaludos,\nEquipo COBRA-MAX"
                send_mail(subject, message, from_email, [u.email])
            except Exception:
                logger.exception('Error enviando email de aprobación al cobrador')
        messages.success(request, f'Cobrador {u.get_full_name() or u.username} aprobado correctamente')
        return redirect('pending_cobradores')

    return render(request, 'usuarios/confirm_approve.html', {'user_obj': u})


@login_required
@require_roles(['admin', 'oficina'])
def reject_cobrador(request, user_id):

    try:
        u = User.objects.get(pk=user_id, tipo_usuario='cobrador')
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('pending_cobradores')

    if request.method == 'POST':
        username = u.username
        # Registrar auditoría antes de eliminar
        try:
            ActionLog.objects.create(
                actor=request.user,
                target_user=u,
                action='reject_cobrador',
                detail=f'Cobrador rechazado por {request.user.username}'
            )
        except Exception:
            logger.exception('Error registrando ActionLog al rechazar cobrador')

        # Notificar por email (si está configurado)
        if u.email:
            try:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
                subject = 'Registro rechazado - COBRA-MAX'
                message = f"Hola {u.get_full_name() or u.username},\n\nLamentamos informarte que tu registro como cobrador ha sido rechazado por el equipo de COBRA-MAX.\n\nSi crees que hubo un error, contacta con soporte.\n\nSaludos,\nEquipo COBRA-MAX"
                send_mail(subject, message, from_email, [u.email])
            except Exception:
                logger.exception('Error enviando email de rechazo al cobrador')

        u.delete()
        messages.success(request, f'Cobrador {username} rechazado y eliminado')
        return redirect('pending_cobradores')

    return render(request, 'usuarios/confirm_reject.html', {'user_obj': u})