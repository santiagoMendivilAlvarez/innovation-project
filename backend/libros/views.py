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


def book_search(request):
    query = request.GET.get('q', '')
    book_details = {}

    if query:
        book_details = api.fetch_book_details(query)
    
    return render(request, 'book_search.html', {'book_details': book_details, 'query': query})
