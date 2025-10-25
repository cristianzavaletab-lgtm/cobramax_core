from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def require_roles(allowed_roles):
    """Decorador para vistas: permite acceso solo si request.user.tipo_usuario está en allowed_roles.

    Uso:
        @login_required
        @require_roles(['admin', 'oficina'])
        def view(...):
            ...

    Redirige a 'dashboard' con mensaje de error si no tiene permisos.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or getattr(user, 'tipo_usuario', None) not in allowed_roles:
                messages.error(request, 'No tienes permisos para acceder a esta página')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
