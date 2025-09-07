from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Libro(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=100, verbose_name="Autor")
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_publicacion = models.DateField(verbose_name="Fecha de Publicación")
    paginas = models.PositiveIntegerField(verbose_name="Número de Páginas")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    calificacion = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        blank=True,
        null=True,
        verbose_name="Calificación"
    )
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.autor}"
