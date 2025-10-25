# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'tipo_usuario', 'is_active', 'date_joined')
    list_filter = ('tipo_usuario', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Información COBRA-MAX', {
            'fields': ('tipo_usuario', 'telefono', 'direccion')  # Quitar 'zona' de aquí
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información COBRA-MAX', {
            'fields': ('tipo_usuario', 'telefono', 'direccion')  # Quitar 'zona' de aquí también
        }),
    )