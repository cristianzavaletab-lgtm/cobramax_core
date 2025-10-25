from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from zonas.models import Zona, Caserio, Departamento, Provincia, Distrito

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class RegistroClienteForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Nombre', max_length=50, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(label='Apellido', max_length=50, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class':'form-control'}))
    dni = forms.CharField(label='DNI', max_length=12, widget=forms.TextInput(attrs={'class':'form-control'}))
    telefono = forms.CharField(label='Teléfono', max_length=20, widget=forms.TextInput(attrs={'class':'form-control'}))
    direccion = forms.CharField(label='Dirección', widget=forms.Textarea(attrs={'class':'form-control', 'rows':2}))
    departamento = forms.ModelChoiceField(label='Departamento', queryset=Departamento.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_departamento'}))
    provincia = forms.ModelChoiceField(label='Provincia', queryset=Provincia.objects.none(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_provincia'}))
    distrito = forms.ModelChoiceField(label='Distrito', queryset=Distrito.objects.none(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_distrito'}))
    zona = forms.ModelChoiceField(label='Zona', queryset=Zona.objects.filter(activa=True), widget=forms.Select(attrs={'class':'form-select', 'id':'id_zona'}))
    caserio = forms.ModelChoiceField(label='Caserío', queryset=Caserio.objects.filter(activa=True), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_caserio'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('El nombre de usuario ya está en uso')
        return username

    def clean(self):
        """Evitar que el formulario reciba un 'tipo_usuario' malicioso en POST."""
        cleaned = super().clean()
        tipo = self.data.get('tipo_usuario')
        if tipo and tipo in ['admin', 'oficina']:
            raise forms.ValidationError('No está permitido asignar roles administrativos desde el registro público')

        # Validación de coherencia geográfica (si se han enviado campos)
        departamento = cleaned.get('departamento')
        provincia = cleaned.get('provincia')
        distrito = cleaned.get('distrito')
        caserio = cleaned.get('caserio')

        # provincia pertenece a departamento
        if provincia and departamento and provincia.departamento_id != departamento.id:
            raise forms.ValidationError('La provincia seleccionada no pertenece al departamento elegido')

        # distrito pertenece a provincia
        if distrito and provincia and distrito.provincia_id != provincia.id:
            raise forms.ValidationError('El distrito seleccionado no pertenece a la provincia elegida')

        # caserio pertenece a distrito
        if caserio and distrito and caserio.distrito_id != distrito.id:
            raise forms.ValidationError('El caserío seleccionado no pertenece al distrito elegido')

        return cleaned


class RegistroCobradorForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Nombre', max_length=50, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(label='Apellido', max_length=50, required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class':'form-control'}))
    telefono = forms.CharField(label='Teléfono', max_length=20, widget=forms.TextInput(attrs={'class':'form-control'}))
    departamento = forms.ModelChoiceField(label='Departamento', queryset=Departamento.objects.all(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_departamento_c'}))
    provincia = forms.ModelChoiceField(label='Provincia', queryset=Provincia.objects.none(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_provincia_c'}))
    distrito = forms.ModelChoiceField(label='Distrito', queryset=Distrito.objects.none(), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_distrito_c'}))
    zona = forms.ModelChoiceField(label='Zona', queryset=Zona.objects.filter(activa=True), widget=forms.Select(attrs={'class':'form-select', 'id':'id_zona_c'}))
    caserio = forms.ModelChoiceField(label='Caserío', queryset=Caserio.objects.filter(activa=True), required=False, widget=forms.Select(attrs={'class':'form-select', 'id':'id_caserio_c'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('El nombre de usuario ya está en uso')
        return username

    def clean(self):
        """Defensa adicional: si alguien intenta inyectar 'tipo_usuario' en el POST,
        rechazamos la petición (registro público no puede asignar roles elevados).
        """

        cleaned = super().clean()
        # self.data contiene los datos brutos de POST; si trae 'tipo_usuario' y
        # es un rol no permitido, lanzamos error.
        tipo = self.data.get('tipo_usuario')
        if tipo and tipo in ['admin', 'oficina']:
            raise forms.ValidationError('No está permitido asignar roles administrativos desde el registro público')

        # Validación geográfica para cobrador (mismos checks que cliente)
        departamento = cleaned.get('departamento')
        provincia = cleaned.get('provincia')
        distrito = cleaned.get('distrito')
        caserio = cleaned.get('caserio')

        if provincia and departamento and provincia.departamento_id != departamento.id:
            raise forms.ValidationError('La provincia seleccionada no pertenece al departamento elegido')
        if distrito and provincia and distrito.provincia_id != provincia.id:
            raise forms.ValidationError('El distrito seleccionado no pertenece a la provincia elegida')
        if caserio and distrito and caserio.distrito_id != distrito.id:
            raise forms.ValidationError('El caserío seleccionado no pertenece al distrito elegido')

        return cleaned
