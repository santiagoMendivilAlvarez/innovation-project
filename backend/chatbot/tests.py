"""
Tests for the Chatbot application models.
"""
from django.test 		 import TestCase
from django.contrib.auth import get_user_model
from chatbot.models 	 import ConversacionChat, MensajeChat, TiposEstado
User = get_user_model()


class ConversacionChatModelTest(TestCase):
	def setUp(self: 'ConversacionChatModelTest') -> None:
		self.user = User.objects.create_user(username = 'testuser',
									    	 password = 'testpass')
		self.conversacion: ConversacionChat = ConversacionChat.objects.create(
			usuario				= self.user,
			titulo_conversacion = 'Test Conversation',
			estado				= TiposEstado.ACTIVA
		)

	def test_conversacion_fields(self: 'ConversacionChatModelTest') -> None:
		self.assertEqual(self.conversacion.usuario, self.user)
		self.assertEqual(self.conversacion.titulo_conversacion, 'Test Conversation')
		self.assertEqual(self.conversacion.estado, TiposEstado.ACTIVA)
		self.assertIsNotNone(self.conversacion.fecha_creacion)
		self.assertIsNotNone(self.conversacion.ultima_actualizacion)

	def test_estado_choices(self: 'ConversacionChatModelTest') -> None:
		self.conversacion.estado = TiposEstado.CERRADA
		self.conversacion.save()
		self.assertEqual(self.conversacion.estado, TiposEstado.CERRADA)


class MensajeChatModelTest(TestCase):
	def setUp(self: 'MensajeChatModelTest') -> None:
		self.user = User.objects.create_user(username = 'testuser2',
									   	     password = 'testpass2')
		self.conversacion: ConversacionChat = ConversacionChat.objects.create(
			usuario			    = self.user,
			titulo_conversacion = 'Chat Test',
			estado				= TiposEstado.ACTIVA
		)
		self.mensaje: MensajeChat = MensajeChat.objects.create(
			conversacion   = self.conversacion,
			tipo_mensaje   = 'usuario',
			contenido	   = 'Hola',
			es_del_usuario = True
		)

	def test_mensaje_fields(self: 'MensajeChatModelTest') -> None:
		self.assertEqual(self.mensaje.conversacion, self.conversacion)
		self.assertEqual(self.mensaje.tipo_mensaje, 'usuario')
		self.assertEqual(self.mensaje.contenido, 'Hola, ¿cómo estás?')
		self.assertTrue(self.mensaje.es_del_usuario)
		self.assertIsNotNone(self.mensaje.fecha_envio)

	def test_mensaje_chatbot(self: 'MensajeChatModelTest') -> None:
		mensaje2: MensajeChat = MensajeChat.objects.create(
			conversacion   = self.conversacion,
			tipo_mensaje   = 'chatbot',
			contenido	   = 'Hola soy el chatbot.',
			es_del_usuario = False
		)
		self.assertEqual(mensaje2.tipo_mensaje, 'chatbot')
		self.assertFalse(mensaje2.es_del_usuario)
