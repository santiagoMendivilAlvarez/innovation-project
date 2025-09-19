"""
Views for the authentication app with strict validation and security.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import random
import string
import json
import logging

from requests import request

from .forms import CustomUserCreationForm, LoginForm, ConfirmEmailForm
from .models import CustomUser

logger = logging.getLogger(__name__)

def register_view(request):
    """
    Handle user registration with strict validation.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        csrf_token = request.POST.get('csrfmiddlewaretoken')
        if form.is_valid():
            if 'user_id_temp' in request.session:
                user_id = request.session.get('user_id_temp')
                try:
                    existing_user = CustomUser.objects.get(id=user_id)
                    if not existing_user.email_verificado:
                        messages.warning(request, 
                            f'Ya hay un proceso de verificación activo para {existing_user.email}. '
                            'Revisa tu correo o completa la verificación.')
                        return redirect('confirm_email')
                except CustomUser.DoesNotExist:
                    del request.session['user_id_temp']
                    if 'codigo_verificacion' in request.session:
                        del request.session['codigo_verificacion']
            
            try:
                user = form.save()
                logger.info(f"Usuario registrado: {user.email}")

                codigo_verificacion = ''.join(random.choices(string.digits, k=6))
                request.session['codigo_verificacion'] = codigo_verificacion
                request.session['user_id_temp'] = user.id
                request.session['codigo_timestamp'] = timezone.now().isoformat()
                
                subject = 'Verificación de cuenta - BookieWookie'
                message = f"""
Hola {user.nombre_completo},

¡Bienvenido a BookieWookie! 

Para completar tu registro y activar tu cuenta, necesitamos verificar tu dirección de email.

Tu código de verificación es: {codigo_verificacion}

Este código es válido por 10 minutos.

Si no solicitaste esta cuenta, puedes ignorar este mensaje.

¡Gracias por unirte a nosotros!

Equipo de BookieWookie
                """.strip()
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    logger.info(f"Código de verificación enviado a: {user.email}")
                    
                    messages.success(request, 
                        f'¡Registro exitoso! Hemos enviado un código de verificación a {user.email}. '
                        'Revisa tu correo (incluyendo spam) para completar el proceso.')
                    return redirect('confirm_email')
                    
                except Exception as e:
                    logger.error(f"Error enviando email a {user.email}: {str(e)}")
                    messages.error(request, 
                        'Hubo un problema enviando el email de verificación. '
                        'Por favor, intenta registrarte nuevamente.')
                    user.delete()  
                    
            except ValidationError as e:
                for field, error_list in e.message_dict.items():
                    for error in error_list:
                        messages.error(request, f'{field}: {error}')
                logger.warning(f"Error de validación en registro: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error inesperado en registro: {str(e)}")
                messages.error(request, 
                    'Hubo un error procesando tu registro. Por favor intenta nuevamente.')
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        if "password_mismatch" in error.lower():
                            messages.error(request, "Las contraseñas no coinciden.")
                        else:
                            messages.error(request, error)

                    elif field == "email":
                        if "already exists" in error.lower() or "ya existe" in error.lower():
                            messages.error(request, "Este correo ya está registrado.")
                        else:
                            messages.error(request, f"Correo electrónico: {error}")

                    elif field in ["password1", "password2"]:
                        messages.error(request, f"Contraseña: {error}")

                    else:
                        field_label = form.fields[field].label or field
                        messages.error(request, f"{field_label}: {error}")

                logger.warning(f"Formulario de registro inválido: {form.errors}")
    
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@csrf_protect
def login_view(request):
    """
    Handle user login with better validation and security.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    messages.error(request, 
                        'Tu cuenta no está activada. Por favor verifica tu email primero.')
                    logger.warning(f"Intento de login con cuenta inactiva: {email}")
                    return render(request, 'login.html', {'form': form})
                
                if not user.email_verificado:
                    messages.warning(request, 
                        'Tu email no está verificado. Por favor verifica tu correo electrónico.')
                    return render(request, 'login.html', {'form': form})
                
                if not user.is_profile_complete():
                    messages.warning(request, 
                        'Tu perfil no está completo. Por favor completa tu información.')
                    login(request, user)  
                    return redirect('profile')
                
                login(request, user)
                logger.info(f"Login exitoso: {user.email}")
                
                if not remember_me:
                    request.session.set_expiry(0)  
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                messages.success(request, f'¡Bienvenido de vuelta, {user.nombre_completo}!')
                
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('dashboard')
            
            else:
                messages.error(request, 'Email o contraseña incorrectos.')
                logger.warning(f"Intento de login fallido para: {email}")
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """
    Handle user logout with logging.
    """
    user_email = request.user.email if request.user.is_authenticated else 'Anónimo'
    logout(request)
    logger.info(f"Logout: {user_email}")
    return redirect('home')


@login_required
def dashboard_view(request):
    """
    User dashboard - simple version.
    """
    user = request.user
    intereses_list = user.get_intereses_list()
    
    context = {
        'user': user,
        'intereses': intereses_list,
        'intereses_display': user.get_intereses_display(),
        'total_intereses': len(intereses_list),
        'email_verified': user.email_verificado,
    }

    return render(request, 'dashboard.html', context)


@csrf_protect
def confirm_email_view(request):
    """
    Handle email confirmation with expiration and attempt limits.
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('resend') == 'true':
        try:
            if 'user_id_temp' not in request.session or 'codigo_verificacion' not in request.session:
                return JsonResponse({'success': False, 'message': 'Sesión inválida'})
            
            resend_count = request.session.get('resend_count', 0)
            if resend_count >= 3:
                return JsonResponse({'success': False, 'message': 'Has excedido el límite de reenvíos'})
            
            nuevo_codigo = ''.join(random.choices(string.digits, k=6))
            request.session['codigo_verificacion'] = nuevo_codigo
            request.session['codigo_timestamp'] = timezone.now().isoformat()
            request.session['resend_count'] = resend_count + 1
            
            user_id = request.session.get('user_id_temp')
            user = CustomUser.objects.get(id=user_id)
            
            subject = 'Nuevo código de verificación - BookieWookie'
            message = f"""
Hola {user.nombre_completo},

Tu nuevo código de verificación es: {nuevo_codigo}

Este código es válido por 10 minutos.

Si no solicitaste este código, puedes ignorar este mensaje.

Equipo de BookieWookie
            """.strip()
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f"Nuevo código enviado a: {user.email}")
            return JsonResponse({'success': True, 'message': 'Código reenviado exitosamente'})
            
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
        except Exception as e:
            logger.error(f"Error reenviando código: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Error enviando código'})
    
    if 'user_id_temp' not in request.session or 'codigo_verificacion' not in request.session:
        messages.error(request, 'No hay ningún proceso de verificación activo. Por favor regístrate nuevamente.')
        return redirect('register')
    
    codigo_timestamp = request.session.get('codigo_timestamp')
    if codigo_timestamp:
        try:
            timestamp = timezone.datetime.fromisoformat(codigo_timestamp)
            if timezone.now() - timestamp > timedelta(minutes=10):
                user_id = request.session.get('user_id_temp')
                try:
                    user = CustomUser.objects.get(id=user_id)
                    user.delete()  
                except CustomUser.DoesNotExist:
                    pass
                
                del request.session['codigo_verificacion']
                del request.session['user_id_temp']
                del request.session['codigo_timestamp']
                
                messages.error(request, 'El código de verificación ha expirado. Por favor regístrate nuevamente.')
                return redirect('register')
        except (ValueError, TypeError):
            pass
    
    if 'verification_attempts' not in request.session:
        request.session['verification_attempts'] = 0
    
    if request.method == 'POST':
        request.session['verification_attempts'] += 1
        
        if request.session['verification_attempts'] > 3:
            user_id = request.session.get('user_id_temp')
            try:
                user = CustomUser.objects.get(id=user_id)
                user.delete()
                logger.warning(f"Usuario eliminado por exceder intentos: {user.email}")
            except CustomUser.DoesNotExist:
                pass
            
            del request.session['codigo_verificacion']
            del request.session['user_id_temp']
            del request.session['verification_attempts']
            if 'codigo_timestamp' in request.session:
                del request.session['codigo_timestamp']
            
            messages.error(request, 
                'Has excedido el número máximo de intentos. Por favor regístrate nuevamente.')
            return redirect('register')
        
        codigo_ingresado = request.POST.get('codigo', '').strip()
        codigo_correcto = request.session.get('codigo_verificacion')
        user_id = request.session.get('user_id_temp')
        
        if codigo_ingresado == codigo_correcto:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.email_verificado = True
                user.is_active = True
                user.save()
                
                del request.session['codigo_verificacion']
                del request.session['user_id_temp']
                del request.session['verification_attempts']
                if 'codigo_timestamp' in request.session:
                    del request.session['codigo_timestamp']
                
                login(request, user)
                logger.info(f"Email verificado exitosamente: {user.email}")
                
                messages.success(request, 
                    f'¡Email verificado correctamente! Bienvenido a BookieWookie, {user.nombre_completo}.')
                return redirect('dashboard')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'Usuario no encontrado. Por favor regístrate nuevamente.')
                return redirect('register')
        else:
            attempts_remaining = 3 - request.session['verification_attempts']
            if attempts_remaining > 0:
                messages.error(request, 
                    f'Código incorrecto. Te quedan {attempts_remaining} intentos.')
                logger.warning(f"Código incorrecto para usuario ID: {user_id}")
            else:
                messages.error(request, 'Código incorrecto. Este fue tu último intento.')
    
    user_id = request.session.get('user_id_temp')
    user_email = ''
    attempts_used = request.session.get('verification_attempts', 0)
    attempts_remaining = 3 - attempts_used
    
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
            user_email = user.email
        except CustomUser.DoesNotExist:
            messages.error(request, 'Usuario no encontrado. Por favor regístrate nuevamente.')
            return redirect('register')
    
    context = {
        'user_email': user_email,
        'attempts_remaining': attempts_remaining,
        'attempts_used': attempts_used,
    }
    
    return render(request, 'confirm_email.html', context)


@require_http_methods(["POST"])
def send_verification_code(request):
    """
    Send verification code via email (API endpoint).
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        if email:
            code = get_random_string(6, '0123456789')
            
            try:
                send_mail(
                    'Código de verificación - BookieWookie',
                    f'Tu código de verificación es: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({'success': True, 'message': 'Código enviado'})
            except Exception as e:
                logger.error(f"Error enviando código a {email}: {str(e)}")
                return JsonResponse({'success': False, 'message': 'Error enviando email'})
        
        return JsonResponse({'success': False, 'message': 'Email requerido'})


@login_required
@require_http_methods(["GET"])
def user_data_api(request):
    """
    API endpoint to get user data.
    """

    
    user = request.user
    data = {
        'id': user.id,
        'email': user.email,
        'nombre_completo': user.nombre_completo,
        'universidad': user.get_universidad_display(),
        'universidad_value': user.universidad,
        'carrera': user.carrera,
        'nivel_academico': user.get_nivel_academico_display(),
        'nivel_academico_value': user.nivel_academico,
        'intereses': user.get_intereses_list(),
        'email_verificado': user.email_verificado,
        'suscripcion_activa': user.suscripcion_activa,
        'profile_complete': user.is_profile_complete(),
        'profile_completion': user.get_profile_completion_percentage(),
    }
    return JsonResponse(data)


@login_required 
@require_http_methods(["POST"])
def update_intereses_api(request):
    """
    API endpoint to update user interests with validation.
    """
    try:
        data = json.loads(request.body)
        intereses = data.get('intereses', [])
        
        if len(intereses) > 10:
            return JsonResponse({
                'success': False,
                'message': 'Máximo 10 intereses permitidos'
            })
        
        user = request.user
        user.set_intereses(intereses)
        user.save()
        
        logger.info(f"Intereses actualizados para: {user.email}")
        
        return JsonResponse({
            'success': True, 
            'intereses': user.get_intereses_list(),
            'message': 'Intereses actualizados correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error actualizando intereses: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error actualizando intereses'
        })


def home_view(request):
    """
    Home page with redirect logic.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')