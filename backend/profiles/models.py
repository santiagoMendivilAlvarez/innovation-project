from django.db              import models
from libros.models          import Libro, Categoria
from django.contrib.auth    import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
User = get_user_model()


class TipoRecomendacion(models.TextChoices):
    AMIGO    = 'amigo'   , 'Amigo'
    FAMILIAR = 'familiar', 'Familiar'
    COLEGA   = 'colega'  , 'Colega'
    OTRO     = 'otro'    , 'Otro'


class Recomendacion(models.Model):
    """
    Model that represents a book recommendation made by a user.
    """
    usuario = models.ForeignKey(
        User,
        on_delete    = models.CASCADE,
        related_name = "recomendaciones",
        verbose_name = "Usuario",
        help_text    = "El usuario que hace la recomendación."
    )
    libro = models.ForeignKey(
        Libro,
        on_delete    = models.CASCADE,
        related_name = "recomendaciones",
        verbose_name = "Libro",
        help_text    = "El libro que es recomendado."
    )
    tipo_recomendacion = models.CharField(
        max_length   = 50,
        choices      = TipoRecomendacion.choices,
        verbose_name = "Tipo de Recomendación",
        help_text    = "El tipo de recomendación (amigo, familiar, colega, otro)."
    )
    calificacion_recomendacion = models.FloatField(
        validators   = [MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name = "Calificación de la Recomendación",
        help_text    = "Ingrese la calificación de la recomendación (0.0 a 5.0)."
    )
    razon_recomendacion = models.CharField(
        max_length   = 500,
        verbose_name = "Razón de la Recomendación",
        help_text    = "Explique brevemente la razón de la recomendación (máximo 500 caracteres)."
    )
    fecha_recomendacion = models.DateTimeField(
        auto_now_add  = True,
        verbose_name  = "Fecha de Recomendación",
        help_text     = "La fecha y hora en que se hizo la recomendación."
    )
    vista = models.BooleanField(
        default       = False,
        verbose_name  = "Vista",
        help_text     = "Indica si el usuario ha visto la recomendación."
    )

    class Meta:
        verbose_name        = "Recomendación"
        verbose_name_plural = "Recomendaciones"

    def __str__(self: 'Recomendacion') -> str:
        return f"Recomendación de {self.usuario.username} para {self.libro.titulo}"


class Favorito(models.Model):
    """
    Model that represents a book marked as favorite by a user.
    """
    usuario = models.ForeignKey(
        User,
        on_delete    = models.CASCADE,
        related_name = "favoritos",
        verbose_name = "Usuario",
        help_text    = "El usuario que marcó el libro como favorito."
    )
    libro = models.ForeignKey(
        Libro,
        on_delete    = models.CASCADE,
        related_name = "favoritos",
        verbose_name = "Libro",
        help_text    = "El libro que fue marcado como favorito."
    )
    fecha_favorito = models.DateTimeField(
        auto_now_add  = True,
        verbose_name  = "Fecha de Favorito",
        help_text     = "La fecha y hora en que se marcó el libro como favorito."
    )

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"

    def __str__(self: 'Favorito') -> str:
        return f"{self.usuario.username} - {self.libro.titulo}"


class InteresUsuario(models.Model):
    """
    Model that represents a user's interest in a specific book genre.
    """
    usuario = models.ForeignKey(
        User,
        on_delete    = models.CASCADE,
        related_name = "intereses",
        verbose_name = "Usuario",
        help_text    = "El usuario que tiene el interés."
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete    = models.CASCADE,
        related_name = "intereses_usuarios",
        verbose_name = "Género",
        help_text    = "El género de libro en el que el usuario está interesado."
    )
    nivel_interes = models.IntegerField(
        validators   = [MinValueValidator(1), MaxValueValidator(10)],
        verbose_name = "Nivel de Interés",
        help_text    = "El nivel de interés del usuario en este género (1 a 10)."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add  = True,
        verbose_name  = "Fecha de Creación",
        help_text     = "La fecha y hora en que se creó este interés."
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now      = True,
        verbose_name  = "Fecha de Actualización",
        help_text     = "La fecha y hora de la última actualización de este interés."
    )

    class Meta:
        verbose_name   = "Interés de Usuario"
        verbose_name_plural = "Intereses de Usuario"

    def __str__(self: 'InteresUsuario') -> str:
        return f"{self.usuario.username} (Nivel: {self.nivel_interes})"
