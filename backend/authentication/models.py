"""
Models for the custom user in the authentication app.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import re


class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser with additional fields and strict validation.
    """
    nombre_completo = models.CharField(
        max_length=100,
        blank=False,  
        null=False,   
        verbose_name="Nombre completo",
        validators=[
            MinLengthValidator(2, "El nombre debe tener al menos 2 caracteres")
        ]
    )

    UNIVERSIDAD_CHOICES = [
       ('uacj', 'Universidad Autónoma de Ciudad Juárez'),
        ('utcj', 'Universidad Tecnológica de Ciudad Juárez'),
        ('unitec', 'Universidad Tecnológica de México'),
        ('uabj', 'Universidad Autónoma de Baja California (Campus Juárez)'),
        ('universidad_salto', 'Universidad Politécnica de Ciudad Juárez'),
        ('tec', 'Tecnológico de Monterrey -  Campus Ciudad Juárez'),
        ('otra', 'Otra universidad'),
    ]

    universidad = models.CharField(
        max_length=50,
        blank=False,  
        null=False,
        choices=UNIVERSIDAD_CHOICES,
        verbose_name="Universidad",
        help_text="Selecciona tu universidad"
    )

    carrera = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name="Carrera",
        validators=[
            MinLengthValidator(3, "El nombre de la carrera debe tener al menos 3 caracteres")
        ],
        help_text="Nombre completo de la carrera"
    )

    NIVEL_CHOICES = [
        ('licenciatura', 'Licenciatura'),
        ('maestria', 'Maestría'),
        ('doctorado', 'Doctorado'),
        ('otro', 'Otro')
    ]

    nivel_academico = models.CharField(
        max_length=20,
        blank=False,  
        null=False,   
        choices=NIVEL_CHOICES,
        verbose_name="Nivel Académico",
        help_text="Selecciona tu nivel académico"
    )

    email_verificado = models.BooleanField(
        default=False,
        verbose_name="Email Verificado",
    )

    suscripcion_activa = models.BooleanField(
        default=False,
        verbose_name="Suscripción Activa",
    )

    fecha_suscripcion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Suscripción",
    )

    intereses_usuario = models.TextField(
        blank=True,
        default="[]",
        verbose_name="Intereses personales",
        help_text="Selecciona tus intereses personales"
    )

    email = models.EmailField(
        unique=True,
        blank=False,  
        null=False,   
        verbose_name="Correo electrónico",
        validators=[EmailValidator(message="Ingrese un email válido")],
        help_text="Email único del usuario (obligatorio)."
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )

    ultima_actividad = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actividad"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nombre_completo', 'universidad', 'carrera', 'nivel_academico']

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['universidad']),
            models.Index(fields=['carrera']),
        ]

    def clean(self):
        """
        Validation logic for the model fields.
        """
        super().clean()
        
        if self.nombre_completo:
            if len(self.nombre_completo.strip()) < 2:
                raise ValidationError({'nombre_completo': 'El nombre debe tener al menos 2 caracteres.'})
            
            if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$", self.nombre_completo.strip()):
                raise ValidationError({'nombre_completo': 'El nombre solo puede contener letras, espacios y guiones.'})

        if self.email:
            existing_user = CustomUser.objects.filter(email=self.email).exclude(pk=self.pk)
            if existing_user.exists():
                raise ValidationError({'email': 'Este email ya está registrado.'})

        if self.carrera and len(self.carrera.strip()) < 3:
            raise ValidationError({'carrera': 'El nombre de la carrera debe tener al menos 3 caracteres.'})

        campos_obligatorios = {
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'universidad': self.universidad,
            'carrera': self.carrera,
            'nivel_academico': self.nivel_academico
        }

        for campo, valor in campos_obligatorios.items():
            if campo in ['universidad', 'nivel_academico']:
                if not valor:
                    raise ValidationError({campo: f'Este campo es obligatorio.'})
            else:
                if not valor or not valor.strip():
                    raise ValidationError({campo: f'Este campo es obligatorio.'})

    def save(self, *args, **kwargs):
        """
        Override save method with additional validation.
        """
        if self.nombre_completo:
            self.nombre_completo = ' '.join(self.nombre_completo.strip().split())
        if self.carrera:
            self.carrera = self.carrera.strip()
        if self.email:
            self.email = self.email.lower().strip()

        if not self.username and self.email:
            self.username = self.email.split('@')[0]

        self.full_clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        """
        String representation of the user.
        """
        return f"{self.email} ({self.nombre_completo})"

    def get_intereses_display(self):
        """
        Return a formatted string of user interests.
        """
        try:
            intereses_list = json.loads(self.intereses_usuario) if self.intereses_usuario else []
            if not intereses_list:
                return "Sin intereses definidos"
            return ", ".join(intereses_list)
        except (json.JSONDecodeError, TypeError):
            return "Sin intereses definidos"

    def set_intereses(self, lista_intereses):
        """
        Set user interests from a list with validation.
        """
        if not isinstance(lista_intereses, list):
            raise ValueError("Los intereses deben ser una lista")
        
        cleaned_intereses = []
        for interes in lista_intereses[:20]:  
            interes_clean = str(interes).strip()
            if interes_clean and len(interes_clean) >= 2: 
                cleaned_intereses.append(interes_clean[:50])  
        
        self.intereses_usuario = json.dumps(cleaned_intereses)

    def get_intereses_list(self):
        """
        Get user interests as a Python list.
        """
        try:
            return json.loads(self.intereses_usuario) if self.intereses_usuario else []
        except (json.JSONDecodeError, TypeError):
            return []
        
    def is_profile_complete(self):
        """
        Check if the user's profile is complete.
        """
        required_fields = [self.nombre_completo, self.email, self.universidad, self.carrera, self.nivel_academico]
        return all(field and field.strip() for field in required_fields)
