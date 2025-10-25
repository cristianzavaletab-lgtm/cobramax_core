# notificaciones/forms.py
from django import forms
from .models import Notificacion, PlantillaNotificacion
from clientes.models import Cliente
from zonas.models import Zona


class NotificacionForm(forms.ModelForm):
    """Formulario para crear notificación individual"""
    
    class Meta:
        model = Notificacion
        fields = ['cliente', 'zona', 'tipo', 'mensaje', 'canal']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'zona': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe el mensaje de la notificación...'
            }),
            'canal': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(estado='activo')
        self.fields['zona'].required = False


class NotificacionMasivaForm(forms.Form):
    """Formulario para notificaciones masivas"""
    
    tipo = forms.ChoiceField(
        choices=Notificacion.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Notificación'
    )
    
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escribe el mensaje que se enviará a todos los clientes seleccionados...'
        }),
        label='Mensaje',
        required=False
    )
    
    zona = forms.ModelChoiceField(
        queryset=Zona.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label='Todas las zonas',
        label='Filtrar por Zona'
    )
    
    estado_cliente = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Cliente.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Estado del Cliente'
    )
    
    usar_plantilla = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Usar plantilla predefinida'
    )
    
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaNotificacion.objects.filter(activa=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label='Selecciona una plantilla',
        label='Plantilla'
    )


class PlantillaNotificacionForm(forms.ModelForm):
    """Formulario para gestionar plantillas"""
    
    class Meta:
        model = PlantillaNotificacion
        fields = ['nombre', 'tipo', 'contenido', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la plantilla'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Contenido de la plantilla. Puedes usar variables como {{nombre_cliente}}, {{monto_deuda}}, etc.'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }