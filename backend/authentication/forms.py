"""
Forms for the authentication app.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
import json


class CustomUserCreationForm(UserCreationForm):
    """
    User creation form with all fields.
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label="Correo electrónico *",
        help_text="Email único que usarás para iniciar sesión"
    )
    
    nombre_completo = forms.CharField(
        max_length=100,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre completo'
        }),
        label="Nombre completo *",
        help_text="Mínimo 2 caracteres, solo letras y espacios"
    )
    
    password1 = forms.CharField(
        label="Contraseña *",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Crea una contraseña segura'
        }),
        help_text="Mínimo 8 caracteres"
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña *",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        }),
        help_text="Debe coincidir con la contraseña anterior"
    )
    
    universidad = forms.ChoiceField(
        choices=[('', 'Selecciona tu universidad')] + CustomUser.UNIVERSIDAD_CHOICES,
        required=True,  
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Universidad *",
        help_text="Selecciona tu universidad"
    )
    
    nivel_academico = forms.ChoiceField(
        choices=[('', 'Selecciona tu nivel académico')] + CustomUser.NIVEL_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Nivel académico *",
        help_text="Tu nivel de estudios"
    )
    
    carrera = forms.CharField(
        max_length=150,
        min_length=3,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo de tu carrera'
        }),
        label="Carrera *",
        help_text="Mínimo 3 caracteres"
    )
    
    INTERESES_CHOICES = [
        ('tecnologia_innovacion', 'Tecnología e Innovación'),
        ('ciencias_matematicas', 'Ciencias y Matemáticas'),
        ('ingenieria', 'Ingeniería'),
        ('negocios_emprendimiento', 'Negocios y Emprendimiento'),
        ('arte_diseno', 'Arte y Diseño'),
        ('medicina_salud', 'Medicina y Salud'),
        ('educacion', 'Educación'),
        ('comunicacion_marketing', 'Comunicación y Marketing'),
        ('derecho', 'Derecho y Ciencias Jurídicas'),
        ('psicologia', 'Psicología y Ciencias Sociales'),
        ('deportes_fitness', 'Deportes y Fitness'),
        ('musica_entretenimiento', 'Música y Entretenimiento'),
    ]
    
    intereses_usuario = forms.MultipleChoiceField(
        choices=INTERESES_CHOICES,
        required=False, 
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="¿Cuáles son tus intereses? (Opcional)",
        help_text="Puedes elegir varios o ninguno."
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'nombre_completo', 'password1', 'password2',
            'universidad', 'nivel_academico', 'carrera', 'intereses_usuario'
        )

    def clean_email(self):
        """
        Validate email uniqueness.
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        
        email = email.lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean_nombre_completo(self):
        """
        Validate nombre_completo format.
        """
        nombre = self.cleaned_data.get('nombre_completo')
        if not nombre:
            raise forms.ValidationError("El nombre completo es obligatorio.")
        
        nombre = nombre.strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        
        import re
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$", nombre):
            raise forms.ValidationError("El nombre solo puede contener letras, espacios y guiones.")
        
        return ' '.join(nombre.split())  

    def clean_universidad(self):
        """
        Validate universidad selection.
        """
        universidad = self.cleaned_data.get('universidad')
        if not universidad:
            raise forms.ValidationError("Debes seleccionar una universidad.")
        return universidad

    def clean_nivel_academico(self):
        """
        Validate nivel_academico selection.
        """
        nivel = self.cleaned_data.get('nivel_academico')
        if not nivel:
            raise forms.ValidationError("Debes seleccionar tu nivel académico.")
        return nivel

    def clean_carrera(self):
        """
        Validate carrera.
        """
        carrera = self.cleaned_data.get('carrera')
        if not carrera:
            raise forms.ValidationError("La carrera es obligatoria.")
        
        carrera = carrera.strip()
        if len(carrera) < 3:
            raise forms.ValidationError("El nombre de la carrera debe tener al menos 3 caracteres.")
        
        return carrera

    def clean_intereses_usuario(self):
        """
        Validate interests selection.
        """
        intereses = self.cleaned_data.get('intereses_usuario', [])
        if len(intereses) > 10:
            raise forms.ValidationError("Puedes seleccionar máximo 10 intereses.")
        return intereses

    def save(self, commit=True):
        """
        Save user with custom fields.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        user.nombre_completo = self.cleaned_data['nombre_completo']
        user.universidad = self.cleaned_data['universidad']
        user.nivel_academico = self.cleaned_data['nivel_academico']
        user.carrera = self.cleaned_data['carrera'].strip()
        
        
        intereses_list = self.cleaned_data.get('intereses_usuario', [])
        user.intereses_usuario = json.dumps(intereses_list)
        
        if not user.username:
            user.username = user.email.split('@')[0]
        
        user.is_active = False
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Simple login form.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'username'
        }),
        label="Correo electrónico"
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Mantenerme conectado"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email


class ConfirmEmailForm(forms.Form):
    """
    Simple email confirmation form.
    """
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '123456',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code'
        }),
        label="Código de verificación",
        help_text="Ingresa el código de 6 dígitos que enviamos a tu email"
    )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise forms.ValidationError("El código de verificación es obligatorio.")
        
        if not codigo.isdigit():
            raise forms.ValidationError("El código debe contener solo números.")
        
        if len(codigo) != 6:
            raise forms.ValidationError("El código debe tener exactamente 6 dígitos.")
        
        return codigo

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        }),
        error_messages={
            'required': 'El correo es obligatorio.',
            'invalid': 'Correo inválido.',
        }
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError('No existe cuenta con este correo.')
        return email

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        min_length=8,
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'min_length': 'Mínimo 8 caracteres.',
        }
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        error_messages={
            'required': 'Confirma tu contraseña.',
        }
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        
        if password and confirm and password != confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data