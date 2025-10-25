# chatbot/forms.py
from django import forms
from .models import PreguntaFrecuente, TicketSoporte

class PreguntaFrecuenteForm(forms.ModelForm):
    class Meta:
        model = PreguntaFrecuente
        fields = ['pregunta', 'respuesta', 'categoria', 'palabras_clave', 'activa']
        widgets = {
            'pregunta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa la pregunta frecuente'}),
            'respuesta': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ingresa la respuesta'}),
            'palabras_clave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: pago, factura, internet, servicio'}),
        }
        help_texts = {
            'palabras_clave': 'Separar palabras clave con comas para mejorar las búsquedas',
        }

class TicketSoporteForm(forms.ModelForm):
    class Meta:
        model = TicketSoporte
        fields = ['titulo', 'descripcion', 'prioridad', 'categoria', 'agente_asignado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'agente_asignado': forms.Select(attrs={'class': 'form-control'}),
        }

class BusquedaChatbotForm(forms.Form):
    consulta = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu pregunta aquí...',
            'autocomplete': 'off'
        })
    )