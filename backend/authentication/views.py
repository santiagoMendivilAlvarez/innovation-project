"""
Views for the authentication app with strict validation and security.
"""
import random
import string
import json
import logging
from datetime                       import timedelta
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib                 import messages
from django.core.mail               import send_mail
from django.conf                    import settings
from django.utils.crypto            import get_random_string
from django.http                    import JsonResponse
from django.views.decorators.http   import require_http_methods
from django.views.decorators.csrf   import csrf_protect
from django.core.exceptions         import ValidationError
from django.utils                   import timezone
from .forms                         import CustomUserCreationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .models                        import CustomUser
from core.sessions.session          import SessionSubsystem
_session = SessionSubsystem()


logger = logging.getLogger(__name__)


def _send_email(subject, message, recipient_email):
    """Send email with error handling."""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error("Error enviando email a %s: %s", recipient_email, str(e))
        return False


def _handle_form_errors(request, form):
    """
    Helper: Form error handling messages.
    """
    for field, errors in form.errors.items():
        for error in errors:
            if field == '__all__':
                messages.error(request, error)
            elif field == "email":
                if "already exists" in error.lower() or "ya existe" in error.lower():
                    messages.error(request, "Este correo ya está registrado.")
                else:
                    messages.error(request, f"Correo: {error}")
            elif field in ["password1", "password2"]:
                messages.error(request, f"Contraseña: {error}")
            else:
                field_label = form.fields[field].label or field
                messages.error(request, f"{field_label}: {error}")

def register_view(request):
    """Handle user registration with strict validation."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            if 'user_id_temp' in request.session:
                user_id = request.session.get('user_id_temp')
                try:
                    existing_user = CustomUser.objects.get(id=user_id)
                    if not existing_user.email_verificado:
                        messages.warning(request,
                                         f'Ya hay un proceso de verificación activo para {existing_user.email}. '
                                         'Revisa tu correo o completa la verificación.')
                        return redirect('')
                except CustomUser.DoesNotExist:
                    _session.clean_session_data(
                        request, ['user_id_temp', 'codigo_verificacion'])

            try:
                user = form.save()
                logger.info(f"Usuario registrado: {user.email}")

                codigo_verificacion = _session.generate_verification_code()
                request.session.update({
                    'codigo_verificacion': codigo_verificacion,
                    'user_id_temp': user.id,
                    'codigo_timestamp': timezone.now().isoformat()
                })

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

                if _send_email(subject, message, user.email):
                    logger.info(
                        f"Código de verificación enviado a: {user.email}")
                    messages.success(request,
                                     f'¡Registro exitoso! Hemos enviado un código de verificación a {user.email}. '
                                     'Revisa tu correo (incluyendo spam) para completar el proceso.')
                    return redirect('confirm_email')
                else:
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
            _handle_form_errors(request, form)
            logger.warning(f"Formulario de registro inválido: {form.errors}")

    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


@csrf_protect
def login_view(request):
    """Handle user login with validation and security."""
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
                    logger.warning(
                        f"Intento de login con cuenta inactiva: {email}")
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

                messages.success(
                    request, f'¡Bienvenido de vuelta, {user.nombre_completo}!')

                next_page = request.GET.get('next')
                return redirect(next_page) if next_page else redirect('home')
            else:
                messages.error(request, 'Email o contraseña incorrectos.')
                logger.warning(f"Intento de login fallido para: {email}")
        else:
            _handle_form_errors(request, form)
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Handle user logout with logging."""
    user_email = request.user.email if request.user.is_authenticated else 'Anónimo'
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')


@login_required
def book_search_view(request):
    """
    Book search page with results from Google Books and Amazon.
    """
    from core.api.google_books import GoogleBooksAPI
    from core.api.amazon_books import AmazonBooksAPI

    user = request.user
    search_query = request.GET.get('search', '').strip()
    all_books = []
    google_error = None
    amazon_error = None

    if search_query:
        # Search in Google Books
        google_api = GoogleBooksAPI()
        google_result = google_api.fetch_book_details(search_query)

        if isinstance(google_result, dict) and 'error' in google_result:
            google_error = google_result['error']
        elif isinstance(google_result, list):
            for book in google_result:
                book['source'] = 'Google Books'
                book['book_id'] = book.get('previewLink', '').split(
                    'id=')[-1] if 'previewLink' in book else ''
                all_books.append(book)

        # Search in Amazon
        amazon_api = AmazonBooksAPI()
        amazon_result = amazon_api.fetch_book_details(
            search_query, max_results=10)

        if isinstance(amazon_result, dict) and 'error' in amazon_result:
            amazon_error = amazon_result['error']
        elif isinstance(amazon_result, list):
            for book in amazon_result:
                book['source'] = 'Amazon'
                book['book_id'] = book.get('url', '').split(
                    '/')[-1] if 'url' in book else ''
                all_books.append(book)

    intereses_list = user.get_intereses_list()

    # If there's a search query, redirect to search page
    search_query = request.GET.get('search', '').strip()
    if search_query:
        return redirect(f'/auth/libros/buscar/?search={search_query}')

    context = {
        'user': user,
        'search_query': search_query,
        'books': all_books,
        'total_results': len(all_books),
        'google_error': google_error,
        'amazon_error': amazon_error,
        'has_results': bool(all_books),
    }

    return render(request, 'book_search.html', context)


@login_required
def book_detail_view(request, book_id):
    """
    Book detail page - shows basic book information.
    """
    # For now, we'll just show the title from the query parameter
    book_title = request.GET.get('title', 'Libro sin título')
    book_author = request.GET.get('author', 'Autor desconocido')
    book_source = request.GET.get('source', 'Fuente desconocida')
    book_thumbnail = request.GET.get('thumbnail', '')
    book_price = request.GET.get('price', 'N/A')

    context = {
        'user': request.user,
        'book': {
            'id': book_id,
            'title': book_title,
            'authors': [book_author] if book_author != 'Autor desconocido' else [],
            'source': book_source,
            'thumbnail': book_thumbnail,
            'price': book_price,
        }
    }

    return render(request, 'book_detail.html', context)

    return render(request, 'dashboard.html', context)


@login_required
def book_search_view(request):
    """
    Book search page with results from Google Books and Amazon.
    """
    from core.api.google_books import GoogleBooksAPI
    from core.api.amazon_books import AmazonBooksAPI

    user = request.user
    search_query = request.GET.get('search', '').strip()
    all_books = []
    google_error = None
    amazon_error = None

    if search_query:
        # Search in Google Books
        google_api = GoogleBooksAPI()
        google_result = google_api.fetch_book_details(search_query)

        if isinstance(google_result, dict) and 'error' in google_result:
            google_error = google_result['error']
        elif isinstance(google_result, list):
            for book in google_result:
                book['source'] = 'Google Books'
                book['book_id'] = book.get('previewLink', '').split(
                    'id=')[-1] if 'previewLink' in book else ''
                all_books.append(book)

        # Search in Amazon
        amazon_api = AmazonBooksAPI()
        amazon_result = amazon_api.fetch_book_details(
            search_query, max_results=10)

        if isinstance(amazon_result, dict) and 'error' in amazon_result:
            amazon_error = amazon_result['error']
        elif isinstance(amazon_result, list):
            for book in amazon_result:
                book['source'] = 'Amazon'
                book['book_id'] = book.get('url', '').split(
                    '/')[-1] if 'url' in book else ''
                all_books.append(book)

    context = {
        'user': user,
        'search_query': search_query,
        'books': all_books,
        'total_results': len(all_books),
        'google_error': google_error,
        'amazon_error': amazon_error,
        'has_results': bool(all_books),
    }

    return render(request, 'book_search.html', context)


@login_required
def book_detail_view(request, book_id):
    """
    Book detail page - shows basic book information.
    """
    # For now, we'll just show the title from the query parameter
    book_title = request.GET.get('title', 'Libro sin título')
    book_author = request.GET.get('author', 'Autor desconocido')
    book_source = request.GET.get('source', 'Fuente desconocida')
    book_thumbnail = request.GET.get('thumbnail', '')
    book_price = request.GET.get('price', 'N/A')

    context = {
        'user': request.user,
        'book': {
            'id': book_id,
            'title': book_title,
            'authors': [book_author] if book_author != 'Autor desconocido' else [],
            'source': book_source,
            'thumbnail': book_thumbnail,
            'price': book_price,
        }
    }

    return render(request, 'book_detail.html', context)


@csrf_protect
def confirm_email_view(request):
    """Handle email confirmation with expiration and attempt limits."""

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('resend') == 'true':
        if 'user_id_temp' not in request.session or 'codigo_verificacion' not in request.session:
            return JsonResponse({'success': False, 'message': 'Sesión inválida'})

        resend_count = request.session.get('resend_count', 0)
        if resend_count >= 3:
            return JsonResponse({'success': False, 'message': 'Has excedido el límite de reenvíos'})

        try:
            nuevo_codigo = _session.generate_verification_code()
            request.session.update({
                'codigo_verificacion': nuevo_codigo,
                'codigo_timestamp': timezone.now().isoformat(),
                'resend_count': resend_count + 1
            })

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

            if _send_email(subject, message, user.email):
                logger.info(f"Nuevo código enviado a: {user.email}")
                return JsonResponse({'success': True, 'message': 'Código reenviado exitosamente'})
            else:
                return JsonResponse({'success': False, 'message': 'Error enviando código'})

        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})

    if 'user_id_temp' not in request.session or 'codigo_verificacion' not in request.session:
        messages.error(
            request, 'No hay ningún proceso de verificación activo. Por favor regístrate nuevamente.')
        return redirect('register')

    if _session.check_session_expiration(request, 'codigo_timestamp', 10):
        user_id = request.session.get('user_id_temp')
        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
        except CustomUser.DoesNotExist:
            pass

        _session.clean_session_data(
            request, ['codigo_verificacion', 'user_id_temp', 'codigo_timestamp'])
        messages.error(
            request, 'El código de verificación ha expirado. Por favor regístrate nuevamente.')
        return redirect('register')

    if 'verification_attempts' not in request.session:
        request.session['verification_attempts'] = 0

    if request.method == 'POST':
        request.session['verification_attempts'] += 1

        if request.session['verification_attempts'] > 3:
            user_id = request.session.get('user_id_temp')
            try:
                user = CustomUser.objects.get(id=user_id)
                user.delete()
                logger.warning(
                    f"Usuario eliminado por exceder intentos: {user.email}")
            except CustomUser.DoesNotExist:
                pass

            _session.clean_session_data(request, [
                                'codigo_verificacion', 'user_id_temp', 'verification_attempts', 'codigo_timestamp'])
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

                _session.clean_session_data(request, [
                                    'codigo_verificacion', 'user_id_temp', 'verification_attempts', 'codigo_timestamp'])

                login(request, user)
                logger.info(f"Email verificado exitosamente: {user.email}")
                messages.success(request,
                                 f'Email verificado correctamente! Bienvenido a BookieWookie, {user.nombre_completo}.')
                return redirect('home')

            except CustomUser.DoesNotExist:
                messages.error(
                    request, 'Usuario no encontrado. Por favor regístrate nuevamente.')
                return redirect('register')
        else:
            attempts_remaining = 3 - request.session['verification_attempts']
            if attempts_remaining > 0:
                messages.error(request,
                               f'Código incorrecto. Te quedan {attempts_remaining} intentos.')
            else:
                messages.error(
                    request, 'Código incorrecto. Este fue tu último intento.')
            logger.warning(f"Código incorrecto para usuario ID: {user_id}")

    user_id = request.session.get('user_id_temp')
    user_email = ''
    attempts_used = request.session.get('verification_attempts', 0)
    attempts_remaining = 3 - attempts_used

    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
            user_email = user.email
        except CustomUser.DoesNotExist:
            messages.error(
                request, 'Usuario no encontrado. Por favor regístrate nuevamente.')
            return redirect('register')

    context = {
        'user_email': user_email,
        'attempts_remaining': attempts_remaining,
        'attempts_used': attempts_used,
    }

    return render(request, 'confirm_email.html', context)


"""Password recovery views with validation and security."""


def forgot_password_view(request):
    """Handle forgot password process - step 1: request code"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email, is_active=True)
                codigo = _session.generate_verification_code()

                request.session.update({
                    'reset_email': email,
                    'reset_code': codigo,
                    'reset_timestamp': timezone.now().isoformat()
                })

                subject = 'Código de recuperación - BookieWookie'
                message = f"""
Hola {user.nombre_completo},

Has solicitado restablecer tu contraseña en BookieWookie.

Tu código de verificación es: {codigo}

Este código es válido por 10 minutos.

Si no solicitaste este cambio, puedes ignorar este mensaje.

Equipo de BookieWookie
                """.strip()

                if _send_email(subject, message, email):
                    logger.info(f"Código de recuperación enviado a: {email}")
                    messages.success(request,
                                     f'Se ha enviado un código de verificación a {email}. '
                                     'Revisa tu correo (incluyendo spam).')
                    return redirect('verify_reset_code')
                else:
                    messages.error(request,
                                   'Hubo un problema enviando el código. Por favor intenta nuevamente.')

            except CustomUser.DoesNotExist:
                messages.success(request,
                                 f'Si existe una cuenta con {email}, recibirás un código de verificación.')
                logger.warning(
                    f"Intento de recuperación para email inexistente: {email}")
        else:
            _handle_form_errors(request, form)
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})


def verify_reset_code_view(request):
    """Handle forgot password process - step 2: verify code"""
    if 'reset_email' not in request.session:
        messages.error(
            request, 'Sesión expirada. Por favor solicita un nuevo código.')
        return redirect('forgot_password')

    if _session.check_session_expiration(request, 'reset_timestamp', 10):
        _session.clean_session_data(
            request, ['reset_email', 'reset_code', 'reset_timestamp'])
        messages.error(
            request, 'El código ha expirado. Por favor solicita uno nuevo.')
        return redirect('forgot_password')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()
        codigo_correcto = request.session.get('reset_code')

        if not codigo_ingresado:
            messages.error(
                request, 'Por favor ingresa el código de verificación.')
        elif len(codigo_ingresado) != 6:
            messages.error(request, 'El código debe tener 6 dígitos.')
        elif not codigo_ingresado.isdigit():
            messages.error(request, 'El código solo debe contener números.')
        elif codigo_ingresado == codigo_correcto:
            request.session['code_verified'] = True
            request.session.modified = True
            messages.success(request, 'Código verificado correctamente.')
            return redirect('reset_password')
        else:
            messages.error(
                request, 'Código incorrecto. Verifica e intenta nuevamente.')
            logger.warning(
                f"Código incorrecto para {request.session.get('reset_email')}")

    email = request.session.get('reset_email')
    return render(request, 'verify_reset_code.html', {'email': email})


def reset_password_view(request):
    """Handle forgot password process - step 3: set new password"""
    if 'reset_email' not in request.session:
        messages.error(
            request, 'Sesión expirada. Por favor solicita un nuevo código.')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            email = request.session.get('reset_email')
            try:
                user = CustomUser.objects.get(email=email, is_active=True)
                user.set_password(form.cleaned_data['new_password'])
                user.save()

                _session.clean_session_data(
                    request, ['reset_email', 'reset_code', 'reset_timestamp'])

                logger.info(
                    f"Contraseña restablecida exitosamente para: {user.email}")
                messages.success(request,
                                 '¡Tu contraseña ha sido actualizada correctamente! '
                                 'Ya puedes iniciar sesión con tu nueva contraseña.')
                return redirect('login')

            except CustomUser.DoesNotExist:
                messages.error(
                    request, 'Usuario no encontrado. Por favor solicita un nuevo código.')
                return redirect('forgot_password')
        else:
            _handle_form_errors(request, form)
    else:
        form = ResetPasswordForm()

    email = request.session.get('reset_email')
    return render(request, 'reset_password.html', {'form': form, 'email': email})


@require_http_methods(["POST"])
def send_verification_code(request):
    """Send verification code via email (API endpoint)."""
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'success': False, 'message': 'Email requerido'})

        code = get_random_string(6, '0123456789')

        if _send_email('Código de verificación - BookieWookie',
                       f'Tu código de verificación es: {code}', email):
            return JsonResponse({'success': True, 'message': 'Código enviado'})
        else:
            return JsonResponse({'success': False, 'message': 'Error enviando email'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos inválidos'})


@login_required
@require_http_methods(["GET"])
def user_data_api(request):
    """API endpoint to get user data."""
    user = request.user
    data = {
        'id': user.id,
        'email': user.email,
        'nombre_completo': user.nombre_completo,
        'universidad_display': user.get_universidad_display(),
        'universidad': user.universidad,
        'carrera': user.carrera,
        'nivel_academico_display': user.get_nivel_academico_display(),
        'nivel_academico': user.nivel_academico,
        'intereses': user.get_intereses_list(),
        'email_verificado': user.email_verificado,
        'suscripcion_activa': user.suscripcion_activa,
        'profile_complete': user.is_profile_complete(),
        'profile_completion_percentage': user.get_completion_percentage(),
    }
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def update_intereses_api(request):
    """API endpoint to update user interests with validation."""
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

        logger.info(f"Intereses actualizados para usuario: {user.email}")

        return JsonResponse({
            'success': True,
            'intereses': user.get_intereses_list(),
            'message': 'Intereses actualizados correctamente'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos inválidos'})
    except Exception as e:
        logger.error(f"Error actualizando intereses: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error actualizando intereses'})


@login_required
def recomendaciones_view(request):
    """Vista para mostrar recomendaciones personalizadas de libros"""
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'recomendaciones.html', context)


@login_required
def mi_biblioteca_view(request):
    """Vista para mostrar la biblioteca personal del usuario"""
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'mi_biblioteca.html', context)
