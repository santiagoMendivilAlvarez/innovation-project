import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
from .forms import (
    EditProfileForm, CustomPasswordChangeForm, EditarInteresesForm
)


@login_required
def perfil_view(request):
    return render(request, 'perfil.html')


@login_required
def configuracion_view(request):
    context = {
        'seccion': request.GET.get('seccion', 'datos')
    }
    return render(request, 'configuracion.html', context)


@login_required
def editar_perfil_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✓ Perfil actualizado correctamente')
            return redirect('configuracion')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, 'editar_perfil.html', {'form': form})


@login_required
def cambiar_email(request):
    if request.method == 'POST':
        new_email = request.POST.get('new_email')
        confirm_email = request.POST.get('confirm_email')
        password = request.POST.get('password')
        
        if new_email != confirm_email:
            messages.error(request, 'Los correos electrónicos no coinciden.')
            return redirect('cambia_email')
        
        if not new_email:
            messages.error(request, 'El correo electrónico es obligatorio.')
            return redirect('cambia_email')
        
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, new_email):
            messages.error(request, 'Por favor ingresa un correo electrónico válido.')
            return redirect('cambia_email')

        if new_email == request.user.email:
            messages.error(request, 'El nuevo correo es igual al actual.')
            return redirect('cambia_email')
        
        if User.objects.filter(email=new_email).exists():
            messages.error(request, 'Este correo electrónico ya está en uso.')
            return redirect('cambia_email')
        
        if not request.user.check_password(password):
            messages.error(request, 'Contraseña incorrecta.')
            return redirect('cambia_email')
        
        
        codigo = str(random.randint(100000, 999999))
        
        request.session['email_verification_code'] = codigo
        request.session['new_email'] = new_email
        request.session['code_attempts'] = 3
        
        send_mail(
            'Código de verificación - BookieWookie',
            f'Tu código de verificación es: {codigo}\n\nEste código es válido por 10 minutos.',
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )
        
        messages.success(request, f'Código enviado a {new_email}')
        return redirect('verificar_nuevo_email')

    return render(request, 'cambia_email.html')


@login_required
def verificar_nuevo_email(request):
    new_email = request.session.get('new_email')
    if not new_email:
        messages.error(request, 'Sesión expirada. Intenta de nuevo.')
        return redirect('cambia_email')

    attempts_remaining = request.session.get('code_attempts', 3)
    
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        codigo_correcto = request.session.get('email_verification_code')
        
        if codigo_ingresado == codigo_correcto:
            request.user.email = new_email
            request.user.save()

            del request.session['email_verification_code']
            del request.session['new_email']
            del request.session['code_attempts']
            
            messages.success(request, 'Correo actualizado correctamente.')
            return redirect('configuracion')
        else:
            attempts_remaining -= 1
            request.session['code_attempts'] = attempts_remaining
            
            if attempts_remaining <= 0:
                del request.session['email_verification_code']
                del request.session['new_email']
                messages.error(request, 'Has agotado tus intentos. Intenta de nuevo.')
                return redirect('cambia_email')
            
            messages.error(request, f'Código incorrecto. Te quedan {attempts_remaining} intentos.')

    return render(request, 'verificar_nuevo_email.html', {
        'new_email': new_email,
        'attempts_remaining': attempts_remaining
    })

@login_required
def cambiar_contrasena_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '✓ Contraseña actualizada correctamente')
            return redirect('configuracion')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'cambiar_contrasena.html', {'form': form})


@login_required
def editar_intereses(request):
    intereses_actuales = request.user.get_intereses_list()
    
    if request.method == 'POST':
        form = EditarInteresesForm(request.POST)
        
        if form.is_valid():
            intereses = form.cleaned_data.get('intereses_usuario', [])
            
            if len(intereses) < 3:
                messages.error(request, 'Debes seleccionar al menos 3 géneros.')
            elif len(intereses) > 10:
                messages.error(request, 'Puedes seleccionar máximo 10 géneros.')
            else:
                try:
                    request.user.set_intereses(intereses)
                    request.user.save()
                    messages.success(request, 'Tus intereses han sido actualizados correctamente.')
                    return redirect('configuracion')
                except Exception as e:
                    messages.error(request, f'Error al guardar intereses: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EditarInteresesForm(initial={'intereses_usuario': intereses_actuales})
    
    return render(request, 'editar_intereses.html', {
        'form': form
    })
@login_required
def mi_biblioteca_view(request):
    return render(request, 'mi_biblioteca.html')