from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@example.com')
class CobradorApprovalTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(username='admin1', password='pass1234')
		self.admin.tipo_usuario = 'admin'
		self.admin.is_active = True
		self.admin.save()

		self.cobrador = User.objects.create_user(username='cobrador1', password='cpass1234', email='cob@example.com')
		self.cobrador.tipo_usuario = 'cobrador'
		self.cobrador.is_active = False
		self.cobrador.save()

	def test_approve_cobrador_creates_actionlog_and_sends_email(self):
		self.client.force_login(self.admin)
		resp = self.client.post(reverse('approve_cobrador', args=[self.cobrador.id]))
		self.cobrador.refresh_from_db()
		from .models import ActionLog

		self.assertTrue(self.cobrador.is_active)
		# ActionLog created
		self.assertTrue(ActionLog.objects.filter(target_user=self.cobrador, action='approve_cobrador').exists())
		# Email sent
		self.assertEqual(len(mail.outbox), 1)

	def test_reject_cobrador_creates_actionlog_and_sends_email_and_deletes(self):
		self.client.force_login(self.admin)
		resp = self.client.post(reverse('reject_cobrador', args=[self.cobrador.id]))
		from .models import ActionLog

		# User should be deleted
		with self.assertRaises(User.DoesNotExist):
			User.objects.get(pk=self.cobrador.pk)

		# ActionLog created (target_user may be null after deletion, so check by action)
		self.assertTrue(ActionLog.objects.filter(action='reject_cobrador').exists())
		# Email sent
		self.assertEqual(len(mail.outbox), 1)


class RegistroPublicoSecurityTests(TestCase):
	"""Tests que aseguran que el registro público no puede crear cuentas admin/oficina."""

	def setUp(self):
		# Crear una zona válida para usar en los formularios de registro
		from zonas.models import Zona
		self.zona = Zona.objects.create(nombre='Zona Test', codigo='ZT')

	def test_no_puede_asignar_admin_via_post_cliente(self):
		# Intento de inyectar tipo_usuario=admin en el POST de registro de cliente
		resp = self.client.post('/', data={
			'action': 'registrar_cliente',
			'username': 'testuser1',
			'password': 'testpass123',
			'first_name': 'Test',
			'last_name': 'User',
			'dni': '12345678',
			'telefono': '987654321',
			'direccion': 'Calle Falsa 123',
			'zona': str(self.zona.id),
			'tipo_usuario': 'admin'
		}, follow=True)

		# El formulario debe rechazar intentos de inyección de roles administrativos;
		# no se debe crear el usuario.
		from django.contrib.auth import get_user_model
		User = get_user_model()
		u = User.objects.filter(username='testuser1').first()
		self.assertIsNone(u)

	def test_no_puede_asignar_oficina_via_post_cobrador(self):
		# Intento de inyectar tipo_usuario=oficina en el POST de registro de cobrador
		resp = self.client.post('/', data={
			'action': 'registrar_cobrador',
			'username': 'cobtest1',
			'password': 'cobpass123',
			'first_name': 'Cob',
			'last_name': 'Test',
			'telefono': '987000111',
			'zona': str(self.zona.id),
			'tipo_usuario': 'oficina'
		}, follow=True)

		from django.contrib.auth import get_user_model
		User = get_user_model()
		u = User.objects.filter(username='cobtest1').first()
		self.assertIsNone(u)


class RegistrationAutoLoginTests(TestCase):
	"""Pruebas para el comportamiento de auto-login tras el registro del cliente.

	Verificamos ambos escenarios:
	- Por defecto (AUTO_LOGIN_AFTER_REGISTER=False) el usuario no queda autenticado y se
	  redirige a la página de login.
	- Con la opción activada, el usuario queda autenticado y se redirige al dashboard.
	"""

	def setUp(self):
		from zonas.models import Zona
		self.zona = Zona.objects.create(nombre='Zona Auto', codigo='ZA')

	def test_no_auto_login_por_defecto(self):
		resp = self.client.post('/', data={
			'action': 'registrar_cliente',
			'username': 'autotest1',
			'password': 'passauto1',
			'first_name': 'Auto',
			'last_name': 'Login',
			'dni': '22222222',
			'telefono': '900000000',
			'direccion': 'Av. Prueba 1',
			'zona': str(self.zona.id),
		}, follow=True)

		# Por defecto no debe crearse sesión
		self.assertFalse('_auth_user_id' in self.client.session)
		# Y redirige al login
		self.assertContains(resp, 'Ya puedes iniciar sesi', status_code=200)

	@override_settings(AUTO_LOGIN_AFTER_REGISTER=True)
	def test_auto_login_activado(self):
		resp = self.client.post('/', data={
			'action': 'registrar_cliente',
			'username': 'autotest2',
			'password': 'passauto2',
			'first_name': 'Auto2',
			'last_name': 'Login2',
			'dni': '33333333',
			'telefono': '900000001',
			'direccion': 'Av. Prueba 2',
			'zona': str(self.zona.id),
		}, follow=True)

		# Con la configuración activa debe existir sesión
		self.assertTrue('_auth_user_id' in self.client.session)
		# Redirige al dashboard
		self.assertContains(resp, 'Dashboard', status_code=200)
