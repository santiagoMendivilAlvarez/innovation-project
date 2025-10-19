"""
Views for the libros app.
"""
from datetime import datetime
from django.shortcuts               import render, redirect
from django.contrib.auth            import get_user_model
from .models                        import Libro, Categoria
from django.http                    import HttpResponse, JsonResponse, HttpRequest
from django.views.decorators.http   import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models               import QuerySet, Q, Count
from libros.models                  import Libro
from core.api.google_books          import GoogleBooksAPI
from core.api.amazon_books          import AmazonBooksAPI, AmazonBooksAPIAlternative
google_api      = GoogleBooksAPI()
amazon_api      = AmazonBooksAPI()
amazon_rapidapi = AmazonBooksAPIAlternative()

@require_http_methods(["GET"])
def books_by_category_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint that returns books filtered by category.
    
    Endpoint de API que retorna libros filtrados por categoría.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        JsonResponse: JSON with books from the requested category.
    """
    category_id = request.GET.get('categoria_id')
    
    if not category_id:
        return JsonResponse({'error': 'categoria_id es requerido'}, status=400)
    
    try:
        category = get_object_or_404(Categoria, id=category_id, activa=True)
        books = Libro.objects.filter(categoria=category).values(
            'id', 'titulo', 'autor', 'isbn', 'precio', 
            'calificacion', 'disponible', 'imagen_url'
        )
        
        return JsonResponse({
            'categoria': {
                'id': category.id,
                'nombre': category.nombre,
                'descripcion': category.descripcion
            },
            'total_libros': books.count(),
            'libros': list(books)
        })
        
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)

@require_http_methods(["GET"])
def category_statistics_api(request: HttpRequest) -> JsonResponse:
    """
    API endpoint that returns category statistics.
    
    Endpoint de API que retorna estadísticas de categorías.
    
    Returns:
        JsonResponse: Complete statistics of all categories.
    """
    categories = Categoria.objects.filter(activa=True).annotate(
        total_libros=Count('libros'),
    ).values('id', 'nombre', 'descripcion', 'total_libros')
    
    total_books_system = Libro.objects.count()
    total_active_categories = categories.count()
    
    statistics = {
        'total_categorias': total_active_categories,
        'total_libros_sistema': total_books_system,
        'categorias': list(categories.order_by('-total_libros')),
        'categoria_mas_popular': categories.order_by('-total_libros').first() if categories else None
    }
    
    return JsonResponse(statistics)

def books(request: HttpRequest) -> HttpResponse:
    """
    Display all books.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered response containing all books and users.
    """
    categorias = Categoria.objects.filter(
        activa=True
    ).annotate(
        total_libros=Count('libros', filter=Q(libros__disponible=True))
    ).order_by('nombre')

    categorias_con_libros = []

    for categoria in categorias:
        libros_destacados = categoria.libros.filter(
            disponible=True
        ).order_by('-calificacion')[:6]

        categorias_con_libros.append({
            'categoria': categoria,
            'libros': libros_destacados,
            'total': categoria.total_libros,
        })

    context = {
        'categorias_con_libros': categorias_con_libros,
        'total_categorias': categorias.count(),
        'usuarios': get_user_model().objects.all(),
    }

    return render(request, 'libros.html', context)

def home_view(request: HttpRequest) -> HttpResponse:
    """
    This is the home view for the whole website.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered response for the home view.
    """
    context = {}
    if request.user.is_authenticated:
        context.update({
            'intereses': request.user.get_intereses_list(),
            'total_intereses': len(request.user.get_intereses_list()),
            'intereses_display': request.user.get_intereses_display(),
            'email_verified': request.user.email_verificado
        })
    last_ten_books = Libro.objects.all().order_by('-fecha_creacion')[:10]
    
    context.update({
        'user': request.user,
        'last_ten_books': last_ten_books
    })
    return render(request, 'dashboard.html', context)


def book_search_view(request):
    """
    Book search: database first, then Google Books and Amazon APIs.
    """
    from core.api.google_books import GoogleBooksAPI
    from core.api.amazon_books import AmazonBooksAPI
    # user = request.user
    search_query = request.GET.get('search', '').strip()
    
    all_books = []
    db_books = []
    google_error = None
    amazon_error = None

    if search_query:
        db_books = Libro.objects.filter(
            Q(titulo__icontains=search_query) |
            Q(autor__icontains=search_query) |
            Q(isbn__icontains=search_query)
        ).order_by('-fecha_creacion')

        for book in db_books:
            all_books.append({
                'source': 'Database',
                'book_id': book.id,
                'title': book.titulo,
                'authors': [book.autor] if book.autor else [],
                'description': book.descripcion,
                'thumbnail': book.imagen_portada.url if book.imagen_portada else '',
                'isbn': book.isbn,
                'is_local': True, 
                'book_object': book 
            })

        if not db_books:
            google_api = GoogleBooksAPI()
            google_result = google_api.fetch_book_details(search_query)

            if isinstance(google_result, dict) and 'error' in google_result:
                google_error = google_result['error']
            elif isinstance(google_result, list):
                for book in google_result:
                    book['source'] = 'Google Books'
                    book['is_local'] = False
                    all_books.append(book)

        if not db_books and not all_books:
            amazon_api = AmazonBooksAPI()
            amazon_result = amazon_api.fetch_book_details(search_query, max_results=10)

            if isinstance(amazon_result, dict) and 'error' in amazon_result:
                amazon_error = amazon_result['error']
            elif isinstance(amazon_result, list):
                for book in amazon_result:
                    book['source'] = 'Amazon'
                    book['is_local'] = False
                    all_books.append(book)

    context = {
        'search_query': search_query,
        'books': all_books,
        'total_results': len(all_books),
        'db_results': len(db_books),
        'google_error': google_error,
        'amazon_error': amazon_error,
        'has_results': bool(all_books),
    }

    return render(request, 'book_search.html', context)


@require_http_methods(["GET"])
def book_search_api(request):
    """
    API endpoint for book search that returns JSON.
    """
    query = request.GET.get('q', '')
    source = request.GET.get('source', 'all')
    max_results = int(request.GET.get('max_results', 10))
    
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)
    
    results = {
        'query': query,
        'google_books': {},
        'amazon_books': {},
        'combined_results': []
    }
    
    if source in ['google', 'all']:
        google_result = google_api.fetch_book_details(query)
        results['google_books'] = google_result
        
        # Add Google book to combined results if found
        if 'title' in google_result and google_result['title'] != 'N/A':
            combined_book = {
                'source': 'google',
                'title': google_result.get('title', 'N/A'),
                'authors': google_result.get('authors', []),
                'description': google_result.get('description', 'N/A'),
                'thumbnail': google_result.get('thumbnail', ''),
                'publisher': google_result.get('publisher', 'N/A'),
                'published_date': google_result.get('publishedDate', 'N/A'),
                'page_count': google_result.get('pageCount', 'N/A'),
                'categories': google_result.get('categories', [])
            }
            results['combined_results'].append(combined_book)
    
    if source in ['amazon', 'all']:
        amazon_result = amazon_api.search_books(query, max_results=max_results)
        results['amazon_books'] = amazon_result
        
        # Add Amazon books to combined results
        if 'books' in amazon_result:
            for book in amazon_result['books']:
                combined_book = {
                    'source': 'amazon',
                    'title': book.get('title', 'N/A'),
                    'authors': book.get('authors', []),
                    'description': book.get('description', 'N/A'),
                    'image_url': book.get('image_url', ''),
                    'price': book.get('price', 'N/A'),
                    'rating': book.get('rating', 'N/A'),
                    'amazon_url': book.get('amazon_url', ''),
                    'publication_date': book.get('publication_date', 'N/A')
                }
                results['combined_results'].append(combined_book)
    
    return JsonResponse(results)


def amazon_book_details(request, asin):
    """
    Get detailed information about a specific Amazon book.
    """
    book_details = amazon_api.get_book_details(asin)
    
    context = {
        'book_details': book_details,
        'asin': asin
    }
    
    return render(request, 'amazon_book_details.html', context)


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

def categorias_listado(request: HttpRequest) -> HttpResponse:
    """
    Muestra todas las categorías con estadísticas.
    """
    categorias = Categoria.objects.filter(
        activa=True
    ).annotate(
        total_libros=Count('libros', filter=Q(libros__disponible=True)),
        calificacion_promedio=Avg('libros__calificacion', filter=Q(libros__disponible=True))
    ).order_by('orden', 'nombre')

    context = {
        'categorias': categorias,
        'total_categorias': categorias.count(),
        'total_libros': Libro.objects.filter(disponible=True).count(),
    }
    return render(request, 'categorias_listado.html', context)


def categoria_detalle(request: HttpRequest, categoria_id: int) -> HttpResponse:
    """
    Muestra todos los libros de una categoría específica.
    """
    categoria = get_object_or_404(Categoria, id=categoria_id, activa=True)
    
    # Obtener parámetros de filtrado
    orden = request.GET.get('orden', '-calificacion')
    busqueda = request.GET.get('busqueda', '').strip()
    
    # Validar orden
    ordenes_validas = ['titulo', '-titulo', 'precio', '-precio', 'calificacion', '-calificacion']
    if orden not in ordenes_validas:
        orden = '-calificacion'
    
    # Obtener libros
    libros = categoria.libros.filter(disponible=True)
    
    if busqueda:
        libros = libros.filter(
            Q(titulo__icontains=busqueda) |
            Q(autor__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    libros = libros.order_by(orden)
    
    # Estadísticas
    stats = {
        'total_libros': libros.count(),
        'calificacion_promedio': libros.aggregate(Avg('calificacion'))['calificacion__avg'] or 0,
        'precio_minimo': libros.aggregate(models.Min('precio'))['precio__min'] or 0,
        'precio_maximo': libros.aggregate(models.Max('precio'))['precio__max'] or 0,
    }
    
    context = {
        'categoria': categoria,
        'libros': libros,
        'estadisticas': stats,
        'busqueda': busqueda,
        'orden': orden,
    }
    return render(request, 'categoria_detalle.html', context)


def libros_por_categoria_vista(request: HttpRequest) -> HttpResponse:
    """
    Vista exploratoria con todas las categorías y sus libros destacados.
    """
    categorias = Categoria.objects.filter(activa=True).annotate(
        total_libros=Count('libros', filter=Q(libros__disponible=True))
    ).order_by('orden', 'nombre')
    
    # Preparar datos de categorías con libros destacados
    categorias_con_libros = []
    for cat in categorias:
        libros_destacados = cat.libros.filter(
            disponible=True,
            calificacion__isnull=False
        ).order_by('-calificacion')[:6]
        
        categorias_con_libros.append({
            'categoria': cat,
            'libros': libros_destacados,
            'total': cat.total_libros(),
        })
    
    context = {
        'categorias_con_libros': categorias_con_libros,
    }
    return render(request, 'libros_por_categoria.html', context)


@require_http_methods(["GET"])
def api_categorias(request: HttpRequest) -> JsonResponse:
    """
    API endpoint que retorna todas las categorías en JSON.
    """
    categorias = Categoria.objects.filter(activa=True).annotate(
        total_libros=Count('libros', filter=Q(libros__disponible=True))
    ).values('id', 'nombre', 'descripcion', 'icono', 'color', 'total_libros')
    
    return JsonResponse({
        'total': categorias.count(),
        'categorias': list(categorias)
    })


@require_http_methods(["GET"])
def api_libros_categoria(request: HttpRequest) -> JsonResponse:
    """
    API endpoint que retorna libros de una categoría específica.
    """
    categoria_id = request.GET.get('categoria_id')
    
    if not categoria_id:
        return JsonResponse({'error': 'categoria_id requerido'}, status=400)
    
    categoria = get_object_or_404(Categoria, id=categoria_id, activa=True)
    libros = categoria.libros.filter(disponible=True).values(
        'id', 'titulo', 'autor', 'precio', 'calificacion', 'imagen_url'
    )
    
    return JsonResponse({
        'categoria': {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion,
        },
        'total_libros': libros.count(),
        'libros': list(libros)
    })
