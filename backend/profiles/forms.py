import re
import json
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()


class EditProfileForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        max_length=100,
        min_length=2,
        required=True,
        label="Nombre completo",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo'
        })
    )

    universidad = forms.ChoiceField(
        choices=User.UNIVERSIDAD_CHOICES,
        required=True,
        label="Universidad",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    nivel_academico = forms.ChoiceField(
        choices=User.NIVEL_CHOICES,
        required=True,
        label="Nivel académico",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    carrera = forms.CharField(
        max_length=150,
        min_length=3,
        required=True,
        label="Carrera",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de tu carrera'
        })
    )

    class Meta:
        model = User
        fields = ['nombre_completo', 'universidad', 'nivel_academico', 'carrera']

    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get('nombre_completo')
        if not nombre:
            raise forms.ValidationError("El nombre completo es obligatorio.")
        nombre = nombre.strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$", nombre):
            raise forms.ValidationError("El nombre solo puede contener letras, espacios y guiones.")
        return ' '.join(nombre.split())

    def clean_carrera(self):
        carrera = self.cleaned_data.get('carrera')
        if not carrera:
            raise forms.ValidationError("La carrera es obligatoria.")
        carrera = carrera.strip()
        if len(carrera) < 3:
            raise forms.ValidationError("El nombre de la carrera debe tener al menos 3 caracteres.")
        return carrera


class ChangeEmailForm(forms.Form):
    new_email = forms.EmailField(
        required=True,
        label="Nuevo correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nuevo@correo.com'
        })
    )

    password = forms.CharField(
        required=True,
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        email = self.cleaned_data.get('new_email')
        if not email:
            raise forms.ValidationError("El correo electrónico es obligatorio.")
        email = email.lower().strip()
        
        if email == self.user.email:
            raise forms.ValidationError("El nuevo correo es igual al actual.")
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError("Contraseña incorrecta.")
        return password


class ConfirmEmailChangeForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label="Código de verificación",
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        })
    )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise forms.ValidationError("El código es obligatorio.")
        if not codigo.isdigit():
            raise forms.ValidationError("El código debe contener solo números.")
        if len(codigo) != 6:
            raise forms.ValidationError("El código debe tener 6 dígitos.")
        return codigo


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        })
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )

class EditarInteresesForm(forms.Form):
    intereses_usuario = forms.MultipleChoiceField(
        choices=[],  # Se llenará en __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Selecciona tus géneros favoritos"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir las opciones de géneros literarios
        GENEROS_CHOICES = [
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
        self.fields['intereses_usuario'].choices = GENEROS_CHOICES