from django.db import models
from django.contrib.auth.models import AbstractUser



class CustomUser(AbstractUser):
    universidad = models.CharField(
        max_length   = 150,
        blank        = True,
        null         = True,
        verbose_name = "Universidad",
        help_text    = "Ingrese el nombre de la universidad del usuario (máximo 150 caracteres)."
    )
    carrera = models.CharField(
        max_length   = 150,
        blank        = True,
        null         = True,
        verbose_name = "Carrera",
        help_text    = "Ingrese la carrera del usuario (máximo 150 caracteres)."
    )
    nivel_academico = models.CharField(
        max_length   = 100,
        blank        = True,
        null         = True,
        verbose_name = "Nivel Académico",
        help_text    = "Ingrese el nivel académico del usuario (máximo 100 caracteres)."
    )
    email_verificado = models.BooleanField(
        default      = False,
        verbose_name = "Email Verificado",
        help_text    = "Indica si el email del usuario ha sido verificado."
    )
    suscripcion_activa = models.BooleanField(
        default      = False,
        verbose_name = "Suscripción Activa",
        help_text    = "Indica si el usuario tiene una suscripción activa."
    )
    fecha_suscripcion = models.DateTimeField(
        blank        = True,
        null         = True,
        verbose_name = "Fecha de Suscripción",
        help_text    = "La fecha y hora en que se activó la suscripción del usuario."
    )
