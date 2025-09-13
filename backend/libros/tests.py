"""
Unit tests for the 'libros' app models.
"""
from django.test  import TestCase
from .models 	  import Categoria, Libro, FuenteLibro, Resena


class CategoriaModelTest(TestCase):
	"""
	Test cases for the Categoria model.
	"""
	def test_categoria_creation(self: 'CategoriaModelTest') -> None:
		"""
		Test the creation of a Categoria instance.
		"""
		categoria: Categoria = Categoria.objects.create(
			nombre      = 'Ficción',
			descripcion = 'Libros de ficción',
			activa		= True
		)
		self.assertEqual(categoria.nombre, 'Ficción')
		self.assertTrue(categoria.activa)
		self.assertEqual(str(categoria), 'Ficción')


class LibroModelTest(TestCase):
	"""
	Test cases for the Libro model.
	"""
	def setUp(self: 'LibroModelTest') -> None:
		"""
		Set up a Categoria instance for Libro tests.
		"""
		self.categoria: Categoria = Categoria.objects.create(nombre='Ciencia', activa=True)

	def test_libro_creation(self: 'LibroModelTest') -> None:
		"""
		Test the creation of a Libro instance.
		"""
		libro: Libro = Libro.objects.create(
			categoria         = self.categoria,
			titulo		      = 'El Origen de las Especies',
			autor			  = 'Charles Darwin',
			isbn		      = '1234567890123',
			fecha_publicacion = '1859-11-24',
			paginas 		  = 502,
			precio  		  = 99.99,
			disponible		  = True
		)
		self.assertEqual(libro.titulo, 'El Origen de las Especies')
		self.assertEqual(libro.autor, 'Charles Darwin')
		self.assertEqual(libro.categoria, self.categoria)
		self.assertTrue(libro.disponible)
		self.assertEqual(str(libro), 'El Origen de las Especies - Charles Darwin')

	def test_libro_calificacion(self: 'LibroModelTest') -> None:
		"""
		Test setting and retrieving the calificacion field.
		"""
		libro: Libro = Libro.objects.create(
			categoria         = self.categoria,
			titulo	          = 'Libro Calificado',
			autor		      = 'Autor',
			isbn			  = '9876543210123',
			fecha_publicacion = '2000-01-01',
			paginas           = 100,
			precio            = 10.0,
			calificacion      = 4.5,
			disponible		  = True
		)
		self.assertEqual(libro.calificacion, 4.5)


class FuenteLibroModelTest(TestCase):
	"""
	Test cases for the FuenteLibro model.
	"""
	def setUp(self: 'FuenteLibroModelTest') -> None:
		"""
		Set up a Categoria and Libro instance for FuenteLibro tests.
		"""
		self.categoria: Categoria = Categoria.objects.create(nombre='Educativo', activa=True)
		self.libro: Libro = Libro.objects.create(
			categoria	      = self.categoria,
			titulo			  = 'Matemáticas Básicas',
			autor			  = 'Juan Pérez',
			isbn		      = '1111111111111',
			fecha_publicacion = '2010-05-10',
			paginas     	  = 300,
			precio      	  = 50.0,
			disponible  	  = True
		)

	def test_fuente_libro_creation(self):
		"""
		Test the creation of a FuenteLibro instance.
		"""
		fuente: FuenteLibro = FuenteLibro.objects.create(
			libro      = self.libro,
			plataforma = 'Amazon',
			url_libro  = 'https://amazon.com/libro',
			precio	   = 45.0,
			moneda	   = 'USD',
			disponible = True
		)
		self.assertEqual(fuente.libro, self.libro)
		self.assertEqual(fuente.plataforma, 'Amazon')
		self.assertEqual(fuente.moneda, 'USD')
		self.assertTrue(fuente.disponible)


class ResenaModelTest(TestCase):
	"""
	Test cases for the Resena model.
	"""
	def setUp(self: 'ResenaModelTest') -> None:
		"""
		Set up a Categoria and Libro instance for Resena tests.
		"""
		self.categoria: Categoria = Categoria.objects.create(nombre='Historia', activa=True)
		self.libro: Libro = Libro.objects.create(
			categoria		  = self.categoria,
			titulo			  = 'Historia Universal',
			autor		      = 'Ana Gómez',
			isbn		      = '2222222222222',
			fecha_publicacion = '1999-09-09',
			paginas			  = 400,
			precio			  = 60.0,
			disponible		  = True
		)

	def test_resena_creation(self):
		"""
		Test the creation of a Resena instance.
		"""
		resena: Resena = Resena.objects.create(
			libro			 = self.libro,
			fuente_resena    = 'Goodreads',
			contenido_resena = 'Excelente libro para aprender historia.',
			calificacion	 = 5.0,
			autor_resena	 = 'Pedro López'
		)
		self.assertEqual(resena.libro, self.libro)
		self.assertEqual(resena.fuente_resena, 'Goodreads')
		self.assertEqual(resena.calificacion, 5.0)
		self.assertEqual(resena.autor_resena, 'Pedro López')
