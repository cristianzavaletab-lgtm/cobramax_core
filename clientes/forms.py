# clientes/forms.py
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar clientes.

    Adaptado para los campos actuales del modelo `Cliente`.
    Si prefieres usar campos anidados (usuario.email, usuario.first_name, ...)
    podemos crear un formulario combinado que gestione también el User.
    """

    class Meta:
        model = Cliente
        # Mantener compatibilidad con plantillas antiguas: exponer
        # los nombres que se usan en las vistas y templates
        fields = [
            'usuario', 'nombre', 'apellido', 'dni', 'telefono', 'email',
            'direccion', 'referencia', 'fecha_instalacion', 'zona',
            'plan', 'monto_mensual', 'dia_vencimiento', 'estado'
        ]
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DNI (8 dígitos)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido del cliente'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '999888777'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUC (opcional)'
            }),
            'telefono_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono principal'
            }),
            'telefono_secundario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono secundario (opcional)'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'referencia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Referencia de domicilio (opcional)'
            }),
            'zona': forms.Select(attrs={'class': 'form-control'}),
            'plan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Plan 20 Mbps'
            }),
            'monto_mensual': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'dia_vencimiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31'
            }),
            'fecha_instalacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni and len(dni) != 8:
            raise forms.ValidationError('El DNI debe tener 8 dígitos')
        return dni

    def clean_telefono_principal(self):
        telefono = self.cleaned_data.get('telefono_principal')
        if telefono and len(telefono) not in (7, 9, 10, 11, 12):
            # No conocemos el formato exacto esperado en todas las zonas;
            # validamos una longitud razonable. Ajusta según convenga.
            raise forms.ValidationError('Número de teléfono con longitud inesperada')
        return telefono