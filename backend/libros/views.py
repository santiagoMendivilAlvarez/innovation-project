"""
Views for the libros app.
"""
from django.shortcuts    import render
from django.contrib.auth import get_user_model
from libros.models       import Libro
from core.api.google_books    import GoogleBooksAPI
api = GoogleBooksAPI()


def view(request):
    """
    Sample view to display all books and users.
    """
    context = {
        'libros'  : Libro.objects.all(),
        'usuarios': get_user_model().objects.all()
    }
    return render(request, 'libros.html', context)


