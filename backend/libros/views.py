from django.shortcuts import render
from django.contrib.auth import get_user_model
from libros.models import Libro



def view(request):
    context = {
        'libros': Libro.objects.all(),
        'usuarios': get_user_model().objects.all()
    }

    return render(request, 'libros.html', context)