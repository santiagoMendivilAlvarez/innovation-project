"""
Test cases for the CustomUser model in the authentication app.
"""
from django.test           import TestCase
from django.utils          import timezone
from authentication.models import CustomUser


class CustomUserModelTest(TestCase):
	"""
	Test cases for the CustomUser model.
	"""
	def setUp(self: 'CustomUserModelTest') -> None:
		"""
		Set up a test user with custom fields.
		"""
		self.user: CustomUser = CustomUser.objects.create_user(
			username           = 'testuser',
			password           = 'testpass123',
			universidad        = 'Universidad Nacional',
			carrera            = 'Ingeniería',
			nivel_academico    = 'Licenciatura',
			email              = 'testuser@example.com',
			email_verificado   = True,
			suscripcion_activa = True,
			fecha_suscripcion  = timezone.now()
		)

	def test_custom_fields(self: 'CustomUserModelTest') -> None:
		self.assertEqual(self.user.universidad, 'Universidad Nacional')
		self.assertEqual(self.user.carrera, 'Ingeniería')
		self.assertEqual(self.user.nivel_academico, 'Licenciatura')
		self.assertTrue(self.user.email_verificado)
		self.assertTrue(self.user.suscripcion_activa)
		self.assertIsNotNone(self.user.fecha_suscripcion)

	def test_default_values(self: 'CustomUserModelTest') -> None:
		user2: CustomUser = CustomUser.objects.create_user(
			username = 'user2',
			password = 'pass2',
			email    = 'user2@example.com'
		)
		self.assertFalse(user2.email_verificado)
		self.assertFalse(user2.suscripcion_activa)
		self.assertIsNone(user2.fecha_suscripcion)
