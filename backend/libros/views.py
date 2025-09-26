"""
Views for the libros app.
"""
from django.shortcuts    import render
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Libro
##from core.api.google_books    import GoogleBooksAPI
##api = GoogleBooksAPI()


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
    libros = []
    total_resultados = 0
    
    if query:
        try:
            # Si tienes modelos configurados
            from .models import Libro
            
            libros_queryset = Libro.objects.filter(
                Q(titulo__icontains=query) |
                Q(autor__nombre__icontains=query) 
            ).select_related('autor', 'categoria').distinct()
            
            # SOLUCIÓN: Calcular total ANTES de paginar
            total_resultados = libros_queryset.count()
            
            # Paginación
            paginator = Paginator(libros_queryset, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            libros = page_obj
            
        except ImportError:
            # FALLBACK: Si no tienes modelos, usar datos ficticios
            libros_fake = [
                {'titulo': f'Resultado para "{query}"', 'autor': 'Autor ejemplo', 'isbn': '123456789', 'disponible': True}
            ]
            paginator = Paginator(libros_fake, 10)
            libros = paginator.get_page(1)
            total_resultados = len(libros_fake)
    
    # ALTERNATIVA SEGURA: Usar len() si count() falla
    if hasattr(libros, 'paginator') and hasattr(libros.paginator, 'count'):
        if total_resultados == 0:
            total_resultados = libros.paginator.count
    
    context = {
        'libros': libros,
        'query': query,
        'total_resultados': total_resultados,
    }    
    ##if query:
    ##    book_details = api.fetch_book_details(query)
    return render(request, 'book_search.html', context) ##{'book_details': book_details, 'query': query}, context)
