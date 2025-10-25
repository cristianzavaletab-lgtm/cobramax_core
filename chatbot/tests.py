from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from clientes.models import Cliente
from .models import ConversacionChatbot, MensajeChatbot
import json

User = get_user_model()


class ChatbotSendTests(TestCase):
	def setUp(self):
		# Crear usuario cliente y su registro Cliente
		self.user = User.objects.create_user(username='cli1', password='passcli')
		self.user.tipo_usuario = 'cliente'
		self.user.save()

		# Crear zona válida
		from zonas.models import Zona
		self.zona = Zona.objects.create(nombre='Zona Test', codigo='ZT')

		self.cliente = Cliente.objects.create(
			usuario=self.user,
			nombre='Cli',
			apellido='Uno',
			dni='11111111',
			telefono_principal='900000000',
			direccion='Calle Test',
			zona=self.zona,
			fecha_instalacion='2025-01-01'
		)

	def test_send_without_openai_uses_fallback(self):
		self.client.force_login(self.user)
		url = reverse('chatbot_send')
		resp = self.client.post(url, data={ 'message': 'Hola, necesito ayuda con mi factura' }, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		# Conversación y mensajes creados
		conv = ConversacionChatbot.objects.filter(cliente=self.cliente).first()
		self.assertIsNotNone(conv)
		mensajes = MensajeChatbot.objects.filter(conversacion=conv)
		self.assertGreaterEqual(mensajes.count(), 2)

	def test_out_of_scope_question_returns_scope_message(self):
		self.client.force_login(self.user)
		url = reverse('chatbot_send')
		resp = self.client.post(url, data={ 'message': '¿Cómo hago una pizza margarita?' }, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		# Debe indicar que sólo puede responder sobre COBRA-MAX
		self.assertIn('COBRA-MAX', data.get('respuesta'))

	def test_rate_limit_enforced(self):
		self.client.force_login(self.user)
		url = reverse('chatbot_send')
		# send up to limit
		limit = 5
		from django.test.utils import override_settings
		from django.core.cache import cache
		with override_settings(CHATBOT_RATE_LIMIT=limit, CHATBOT_RATE_WINDOW=60):
			# asegurar que no hay contador previo
			rl_key = f"chatbot_rl:{self.user.pk}"
			cache.delete(rl_key)
			for i in range(limit):
				resp = self.client.post(url, data={ 'message': f'Hola {i}' }, content_type='application/json')
				self.assertEqual(resp.status_code, 200)
			# next one should be rate-limited
			resp2 = self.client.post(url, data={ 'message': 'uno mas' }, content_type='application/json')
			self.assertEqual(resp2.status_code, 429)

	def test_openai_mocked_response(self):
		# Simular que OPENAI_API_KEY está presente y que urllib.request.urlopen devuelve respuesta conocida
		self.client.force_login(self.user)
		url = reverse('chatbot_send')
		from unittest.mock import patch, MagicMock
		fake_response = MagicMock()
		fake_payload = {
			'choices': [
				{'message': {'content': 'Respuesta simulada por OpenAI.'}}
			]
		}
		# make the mock usable as a context manager
		fake_response.__enter__.return_value.read.return_value = json.dumps(fake_payload).encode('utf-8')
		# patch urlopen
		with patch('urllib.request.urlopen', return_value=fake_response):
			with self.settings(OPENAI_API_KEY='sk-test'):
				resp = self.client.post(url, data={ 'message': 'Consulta OpenAI' }, content_type='application/json')
				self.assertEqual(resp.status_code, 200)
				data = resp.json()
				self.assertTrue(data.get('success'))
				self.assertIn('simulada', data.get('respuesta'))

	def test_chatbot_create_ticket_ajax(self):
		# Crear conversación previa
		self.client.force_login(self.user)
		conv = ConversacionChatbot.objects.create(cliente=self.cliente)
		url = reverse('chatbot_create_ticket')
		payload = {'titulo': 'Ayuda via test', 'descripcion': 'Detalle del problema', 'conversacion_id': conv.id}
		resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('success'))
		from .models import TicketSoporte
		ticket_id = data.get('ticket_id')
		self.assertIsNotNone(ticket_id)
		self.assertTrue(TicketSoporte.objects.filter(id=ticket_id).exists())

	def test_auto_ticket_on_ai_failure(self):
		# Simular fallo total de OpenAI y que se cree ticket automático
		self.client.force_login(self.user)
		url = reverse('chatbot_send')
		from unittest.mock import patch
		# Simular que urlopen lanza excepción
		with patch('urllib.request.urlopen', side_effect=Exception('network')):
			with self.settings(OPENAI_API_KEY='sk-test', AUTO_TICKET_ON_AI_ERROR=True, CHATBOT_RETRY_COUNT=0):
				resp = self.client.post(url, data={ 'message': 'Consulta que falla' }, content_type='application/json')
				# la vista devuelve un JSON indicando ai_unavailable y ticket_id
				self.assertEqual(resp.status_code, 200)
				data = resp.json()
				self.assertFalse(data.get('success'))
				self.assertEqual(data.get('error'), 'ai_unavailable')
				self.assertIsNotNone(data.get('ticket_id'))
				from .models import TicketSoporte
				self.assertTrue(TicketSoporte.objects.filter(id=data.get('ticket_id')).exists())
