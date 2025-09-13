"""
Tests for the profiles application models.
"""
from django.test         import TestCase
from django.contrib.auth import get_user_model
from libros.models       import Libro, Categoria
from .models             import Recomendacion, Favorito, InteresUsuario, TipoRecomendacion
User = get_user_model()

class RecomendacionModelTest(TestCase):
    """
	Test case for the Recomendacion model.
    """
    def setUp(self: 'RecomendacionModelTest') -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.categoria: Categoria = Categoria.objects.create(nombre='Fantasía', activa=True)
        self.libro: Libro = Libro.objects.create(
		    categoria		  =  self.categoria,
		    titulo		      =  'El Hobbit',
		    autor			  =  'J.R.R. Tolkien',
		    isbn			  =  '1234567890123',
		    fecha_publicacion = '1937-09-21',
		    paginas			  = 310,
		    precio			  = 39.99,
		    disponible        = True
		)

    def test_recomendacion_creation(self: 'RecomendacionModelTest') -> None:
        recomendacion: 'Recomendacion' = Recomendacion.objects.create(
            usuario					   = self.user,
            libro					   = self.libro,
            tipo_recomendacion		   = TipoRecomendacion.AMIGO,
            calificacion_recomendacion = 4.8,
            razon_recomendacion		   = 'Gran aventura y personajes memorables.',
            vista					   = True
        )
        self.assertEqual(recomendacion.usuario, self.user)
        self.assertEqual(recomendacion.libro, self.libro)
        self.assertEqual(recomendacion.tipo_recomendacion, TipoRecomendacion.AMIGO)
        self.assertEqual(recomendacion.calificacion_recomendacion, 4.8)
        self.assertTrue(recomendacion.vista)
        self.assertEqual(str(recomendacion), f"Recomendación de {self.user.username} para {self.libro.titulo}")

class FavoritoModelTest(TestCase):
	"""
	Test case for the Favorito model.
	"""
	def setUp(self: 'FavoritoModelTest') -> None:
		"""
		Set up a user, category, and book for Favorito tests.
		"""
		self.user = User.objects.create_user(username='favuser', password='favpass')
		self.categoria: Categoria = Categoria.objects.create(nombre='Ciencia Ficción', activa=True)
		self.libro: Libro = Libro.objects.create(
			categoria		  = self.categoria,
			titulo   		  = 'Dune',
			autor    		  = 'Frank Herbert',
			isbn     		  = '9876543210123',
			fecha_publicacion = '1965-08-01',
			paginas   		  = 412, 
			precio    		  = 49.99,
			disponible		  = True
		)

	def test_favorito_creation(self: 'FavoritoModelTest') -> None:
		"""
		Test the creation of a Favorito instance.
		"""
		favorito: Favorito = Favorito.objects.create(
			usuario = self.user,
			libro   = self.libro
		)
		self.assertEqual(favorito.usuario, self.user)
		self.assertEqual(favorito.libro, self.libro)
		self.assertEqual(str(favorito), f"{self.user.username} - {self.libro.titulo}")

class InteresUsuarioModelTest(TestCase):
	def setUp(self: 'InteresUsuarioModelTest') -> None:
		"""
		Set up a user and category for InteresUsuario tests.
		"""
		self.user = User.objects.create_user(username='interesuser', password='interespass')
		self.categoria: Categoria = Categoria.objects.create(nombre='Misterio', activa=True)

	def test_interes_usuario_creation(self: 'InteresUsuarioModelTest') -> None:
		interes: InteresUsuario = InteresUsuario.objects.create(
			usuario		  = self.user,
			categoria	  = self.categoria,
			nivel_interes = 8
		)
		self.assertEqual(interes.usuario, self.user)
		self.assertEqual(interes.categoria, self.categoria)
		self.assertEqual(interes.nivel_interes, 8)
