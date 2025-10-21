"""
Models for the Books application.
"""
from django.db              import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Categoria(models.Model):
    """
    Model that represents a book category.
    """
    nombre = models.CharField(
        max_length   = 100,
        unique       = True,
        verbose_name = "Nombre de la Categoría",
        help_text    = "Ingrese el nombre de la categoría (máximo 100 caracteres)."
    )
    descripcion = models.CharField(
        max_length   = 255,
        blank        = True,
        null         = True,
        verbose_name = "Descripción",
        help_text    = "Ingrese una breve descripción de la categoría."
    )
    activa = models.BooleanField(
        default      = True,
        verbose_name = "Activa",
        help_text    = "Indica si la categoría está activa."
    )

    class Meta:
        verbose_name        = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self: 'Categoria') -> str:
        return self.nombre



class Libro(models.Model):
    """
    Models that represents the book in the system.
    """
    categoria = models.ForeignKey(
        Categoria,
        on_delete    = models.CASCADE,
        related_name = "libros",
        verbose_name = "Categoría",
        help_text    = "La categoría a la que pertenece el libro."
    )
    titulo = models.CharField(
        max_length   = 200,
        verbose_name = "Título",
        help_text    = "Ingrese el título del libro (máximo 200 caracteres)."
    )
    autor = models.CharField(
        max_length   = 100,
        verbose_name = "Autor",
        help_text    = "Ingrese el nombre del autor (máximo 100 caracteres)."
    )
    isbn = models.CharField(
        max_length   = 13,
        unique       = True,
        verbose_name = "ISBN",
        help_text    = "Ingrese el ISBN del libro (13 caracteres)."
    )
    imagen_url = models.CharField(
        max_length   = 255,
        blank        = True,
        null         = True,
        verbose_name = "URL de la Imagen",
        help_text    = "Ingrese la URL de la imagen de portada del libro."
    )
    descripcion = models.TextField(
        blank        = True,
        null         = True,
        verbose_name = "Descripción",
        help_text    = "Ingrese una breve descripción del libro."
    )
    fecha_publicacion = models.DateField(
        verbose_name = "Fecha de Publicación",
        help_text    = "Ingrese la fecha de publicación del libro."
    )
    paginas = models.PositiveIntegerField(
        verbose_name = "Número de Páginas",
        help_text    = "Ingrese el número total de páginas del libro."
    )
    precio = models.DecimalField(
        max_digits     = 10,
        decimal_places = 2,
        verbose_name   = "Precio",
        help_text      = "Ingrese el precio del libro."
    )
    calificacion = models.FloatField(
        validators   = [MinValueValidator(0.0), MaxValueValidator(5.0)],
        blank        = True,
        null         = True,
        verbose_name = "Calificación",
        help_text    = "Ingrese la calificación del libro (0.0 a 5.0)."
    )
    disponible = models.BooleanField(
        default      = True,
        verbose_name = "Disponible",
        help_text    = "Indica si el libro está disponible para la venta."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "Fecha de Creación",
        help_text    = "Fecha y hora en que se creó el registro."
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización",
        help_text="Fecha y hora de la última actualización del registro."
    )

    class Meta:
        verbose_name        = "Libro"
        verbose_name_plural = "Libros"
        ordering            = ['-fecha_creacion']

    def __str__(self: 'Libro') -> str:
        return f"{self.titulo} - {self.autor}"


class FuenteLibro(models.Model):
    """
    Model that represents a source where the book can be found.
    """
    libro = models.ForeignKey(
        Libro,
        on_delete    = models.CASCADE,
        related_name = "fuentes",
        verbose_name = "Libro",
        help_text    = "El libro al que pertenece esta fuente."
    )
    plataforma = models.CharField(
        max_length   = 100,
        verbose_name = "Nombre de la Fuente",
        help_text    = "Ingrese el nombre de la fuente (máximo 100 caracteres)."
    )
    url_libro = models.CharField(
        max_length   = 255,
        verbose_name = "URL de la Fuente",
        help_text    = "Ingrese la URL de la fuente."
    )
    precio = models.FloatField(
        validators   = [MinValueValidator(0.0)],
        verbose_name = "Precio en la Fuente",
        help_text    = "Ingrese el precio del libro en esta fuente."
    )
    moneda = models.CharField(
        max_length   = 10,
        verbose_name = "Moneda",
        help_text    = "Ingrese la moneda del precio (por ejemplo, USD, EUR)."
    )
    disponible = models.BooleanField(
        default      = True,
        verbose_name = "Disponible",
        help_text    = "Indica si el libro está disponible en esta fuente."
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización",
        help_text="Fecha y hora de la última actualización del registro."
    )

    class Meta:
        verbose_name        = "Fuente del Libro"
        verbose_name_plural = "Fuentes del Libro"

    def __str__(self: 'FuenteLibro') -> str:
        return f"Fuente '{self.nombre_fuente}' para {self.libro.titulo}"


class Resena(models.Model):
    """
    Model that represents a review for a book.
    """
    libro = models.ForeignKey(
        Libro,
        on_delete    = models.CASCADE,
        related_name = "resenas",
        verbose_name = "Libro",
        help_text    = "El libro al que pertenece esta reseña."
    )
    fuente_resena = models.CharField(
        max_length   = 100,
        verbose_name = "Fuente de la Reseña",
        help_text    = "Ingrese la fuente de la reseña (máximo 100 caracteres)."
    )
    contenido_resena = models.CharField(
        max_length   = 1064,
        verbose_name = "Contenido de la Reseña",
        help_text    = "Ingrese el contenido de la reseña (máximo 500 caracteres)."
    )
    calificacion = models.FloatField(
        validators   = [MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name = "Calificación",
        help_text    = "Ingrese la calificación de la reseña (0.0 a 5.0)."
    )
    autor_resena = models.CharField(
        max_length   = 100,
        verbose_name = "Autor de la Reseña",
        help_text    = "Ingrese el nombre del autor de la reseña (máximo 100 caracteres)."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "Fecha de Creación",
        help_text    = "Fecha y hora en que se creó el registro."
    )

    def __str__(self: 'Resena') -> str:
        return f"Reseña de {self.autor_resena} para {self.libro.titulo}"

def crear_categorias_por_defecto():
    """Create default categories if they do not exist."""
    categorias = [
        ('Ciencia y Tecnología', 'Libros sobre ciencia, tecnología e innovación'),
        ('Literatura', 'Novelas y obras literarias'),
        ('Historia', 'Libros históricos y biografías'),
        ('Psicología', 'Libros de psicología y comportamiento'),
        ('Filosofía', 'Obras filosóficas y pensamiento'),
        ('Matemáticas', 'Libros de matemáticas'),
        ('Arte y Diseño', 'Libros de arte, diseño y creatividad'),
        ('Negocios', 'Libros de negocios y emprendimiento'),
    ]
    
    for nombre, descripcion in categorias:
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': descripcion, 'activa': True}
        )

"""
Signals to handle post-migration actions.
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def ejecutar_despues_migracion(sender, **kwargs):
    if sender.name == 'libros':
        crear_categorias_por_defecto()