# chatbot/utils.py
import re
from difflib import SequenceMatcher
from .models import PreguntaFrecuente, ConversacionChatbot, TicketSoporte

class ChatbotEngine:
    def __init__(self):
        self.saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hi', 'hello']
        self.despedidas = ['adiós', 'chao', 'hasta luego', 'gracias', 'bye']
        
    def procesar_mensaje(self, mensaje, conversacion):
        mensaje = mensaje.lower().strip()
        
        # Detectar saludos
        if any(saludo in mensaje for saludo in self.saludos):
            return self._generar_saludo()
        
        # Detectar despedidas
        if any(despedida in mensaje for despedida in self.despedidas):
            return self._generar_despedida()
        
        # Buscar en preguntas frecuentes
        respuesta_pf = self._buscar_en_preguntas_frecuentes(mensaje)
        if respuesta_pf:
            return respuesta_pf
        
        # Consultas específicas del sistema
        respuesta_sistema = self._procesar_consultas_sistema(mensaje, conversacion)
        if respuesta_sistema:
            return respuesta_sistema
        
        # Respuesta por defecto
        return self._generar_respuesta_generica()
    
    def _buscar_en_preguntas_frecuentes(self, mensaje):
        """Buscar la mejor coincidencia en preguntas frecuentes"""
        preguntas = PreguntaFrecuente.objects.filter(activa=True)
        mejor_coincidencia = None
        mejor_puntaje = 0
        
        for pf in preguntas:
            # Buscar en pregunta
            puntaje_pregunta = self._calcular_similitud(mensaje, pf.pregunta.lower())
            
            # Buscar en palabras clave
            palabras_clave = [p.strip().lower() for p in pf.palabras_clave.split(',')]
            puntaje_palabras = max([self._calcular_similitud(mensaje, palabra) for palabra in palabras_clave] or [0])
            
            puntaje_total = max(puntaje_pregunta, puntaje_palabras)
            
            if puntaje_total > mejor_puntaje and puntaje_total > 0.6:  # Umbral de similitud
                mejor_puntaje = puntaje_total
                mejor_coincidencia = pf
        
        if mejor_coincidencia:
            # Incrementar contador
            mejor_coincidencia.veces_preguntada += 1
            mejor_coincidencia.save()
            
            return {
                'respuesta': mejor_coincidencia.respuesta,
                'opciones': self._generar_opciones_relacionadas(mejor_coincidencia)
            }
        
        return None
    
    def _procesar_consultas_sistema(self, mensaje, conversacion):
        """Procesar consultas específicas del sistema Cobra-Max"""
        mensaje = mensaje.lower()
        
        # Consultas sobre pagos
        if any(palabra in mensaje for palabra in ['pago', 'pagar', 'deuda', 'cuota', 'vencimiento']):
            return self._procesar_consulta_pagos(mensaje, conversacion)
        
        # Consultas sobre estado de cuenta
        if any(palabra in mensaje for palabra in ['estado', 'cuenta', 'saldo', 'debo']):
            return self._procesar_consulta_estado_cuenta(mensaje, conversacion)
        
        # Consultas sobre contacto
        if any(palabra in mensaje for palabra in ['contacto', 'teléfono', 'email', 'oficina', 'dirección']):
            return self._generar_info_contacto()
        
        # Derivar a agente humano
        if any(palabra in mensaje for palabra in ['humano', 'persona', 'agente', 'operador']):
            return self._derivar_a_agente(conversacion)
        
        return None
    
    def _procesar_consulta_pagos(self, mensaje, conversacion):
        """Procesar consultas sobre pagos"""
        return {
            'respuesta': (
                "💳 **Información sobre Pagos**\n\n"
                "Puedes realizar tus pagos mediante:\n"
                "• 💰 Transferencia bancaria\n"
                "• 📱 Yape/Plín\n"
                "• 🏦 Depósito en agencia\n"
                "• 💵 Efectivo con nuestro cobrador\n\n"
                "¿Necesitas información específica sobre tu deuda o métodos de pago?"
            ),
            'opciones': [
                {'texto': 'Ver mi deuda actual', 'accion': 'consultar_deuda'},
                {'texto': 'Métodos de pago', 'accion': 'metodos_pago'},
                {'texto': 'Hablar con agente', 'accion': 'derivar_agente'}
            ]
        }
    
    def _procesar_consulta_estado_cuenta(self, mensaje, conversacion):
        """Procesar consultas sobre estado de cuenta"""
        # Aquí integraríamos con el módulo de clientes para obtener info real
        return {
            'respuesta': (
                "📊 **Consulta de Estado de Cuenta**\n\n"
                "Para consultar tu estado de cuenta específico, necesito que te identifiques.\n"
                "Puedes:\n"
                "1. Iniciar sesión en tu cuenta\n"
                "2. Contactar a tu cobrador asignado\n"
                "3. Hablar con un agente de soporte"
            ),
            'opciones': [
                {'texto': 'Iniciar sesión', 'accion': 'login'},
                {'texto': 'Contactar cobrador', 'accion': 'contactar_cobrador'},
                {'texto': 'Agente humano', 'accion': 'derivar_agente'}
            ]
        }
    
    def _derivar_a_agente(self, conversacion):
        """Derivar conversación a agente humano"""
        # Crear ticket de soporte
        ticket = TicketSoporte.objects.create(
            conversacion=conversacion,
            titulo=f"Conversación derivada - {conversacion.session_id}",
            descripcion="El usuario solicitó hablar con un agente humano",
            prioridad='media'
        )
        
        conversacion.estado = 'derivada'
        conversacion.save()
        
        return {
            'respuesta': (
                "👨‍💼 **Derivando a Agente Humano**\n\n"
                "He creado un ticket de soporte para que nuestro equipo te contacte.\n"
                f"**Ticket #**{ticket.id}\n\n"
                "Un agente se comunicará contigo pronto. ¿Hay algo más en lo que pueda ayudarte mientras tanto?"
            ),
            'derivar_agente': True
        }
    
    def _generar_saludo(self):
        return {
            'respuesta': (
                "👋 **¡Hola! Soy el asistente virtual de Cobra-Max**\n\n"
                "Estoy aquí para ayudarte con:\n"
                "• 📊 Consultas de estado de cuenta\n"
                "• 💰 Información sobre pagos\n"
                "• 🏢 Datos de contacto\n"
                "• ❓ Preguntas frecuentes\n\n"
                "¿En qué puedo asistirte hoy?"
            ),
            'opciones': [
                {'texto': 'Consultar mi deuda', 'accion': 'consultar_deuda'},
                {'texto': 'Métodos de pago', 'accion': 'metodos_pago'},
                {'texto': 'Preguntas frecuentes', 'accion': 'preguntas_frecuentes'},
                {'texto': 'Contactar soporte', 'accion': 'contactar_soporte'}
            ]
        }
    
    def _generar_despedida(self):
        return {
            'respuesta': (
                "¡Gracias por usar Cobra-Max! 👋\n\n"
                "Recuerda que estoy disponible 24/7 para ayudarte.\n"
                "¡Que tengas un excelente día! 😊"
            )
        }
    
    def _generar_info_contacto(self):
        return {
            'respuesta': (
                "📞 **Información de Contacto**\n\n"
                "**Oficina Principal:**\n"
                "📍 Av. Principal 123, Lima\n"
                "📞 (01) 234-5678\n"
                "📧 soporte@cobramax.com\n\n"
                "**Horario de Atención:**\n"
                "Lunes a Viernes: 8:00 AM - 6:00 PM\n"
                "Sábados: 9:00 AM - 1:00 PM\n\n"
                "¿Necesitas ayuda específica?"
            )
        }
    
    def _generar_respuesta_generica(self):
        return {
            'respuesta': (
                "🤔 No estoy seguro de entender tu pregunta.\n\n"
                "Puedo ayudarte con:\n"
                "• Consultas sobre pagos y deudas\n"
                "• Información de contacto\n"
                "• Preguntas frecuentes\n"
                "• Derivarte a un agente humano\n\n"
                "¿Podrías reformular tu pregunta o elegir una de estas opciones?"
            ),
            'opciones': [
                {'texto': 'Quiero pagar mi deuda', 'accion': 'pagar_deuda'},
                {'texto': 'Consultar estado de cuenta', 'accion': 'estado_cuenta'},
                {'texto': 'Ver preguntas frecuentes', 'accion': 'preguntas_frecuentes'},
                {'texto': 'Hablar con agente', 'accion': 'derivar_agente'}
            ]
        }
    
    def _calcular_similitud(self, texto1, texto2):
        """Calcular similitud entre dos textos"""
        return SequenceMatcher(None, texto1, texto2).ratio()
    
    def _generar_opciones_relacionadas(self, pregunta_frecuente):
        """Generar opciones relacionadas con la pregunta frecuente"""
        opciones_relacionadas = PreguntaFrecuente.objects.filter(
            categoria=pregunta_frecuente.categoria,
            activa=True
        ).exclude(id=pregunta_frecuente.id)[:3]
        
        return [{'texto': pf.pregunta, 'accion': f'pregunta_{pf.id}'} for pf in opciones_relacionadas]