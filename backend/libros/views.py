"""
Views for the libros app.
"""
# pylint: disable=E1101
from django.shortcuts                     import render, get_object_or_404
from django.contrib.auth                  import get_user_model
from django.http                          import HttpResponse, JsonResponse, HttpRequest
from django.views.decorators.http         import require_http_methods
from django.contrib.auth.decorators       import login_required
from django.db.models                     import QuerySet, Q, Count, Avg
from django.db                            import models
from libros.models                        import Libro
from core.api.google_books                import GoogleBooksAPI
from core.api.amazon_books                import AmazonBooksAPI, AmazonBooksAPIAlternative
from core.services.recommendation_service import RecomendationEngine
from .models                              import Libro, Categoria
from profiles.models                      import Favorito
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

    Args:s
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

        # Check favorite status for each book if user is authenticated
        if request.user.is_authenticated:
            for libro in libros_destacados:
                libro.is_favorite = Favorito.objects.filter(
                    usuario=request.user,
                    libro=libro
                ).exists()

        categorias_con_libros.append({
            'categoria': categoria,
            'libros': libros_destacados,
            'total': categoria.total_libros,
        })

    context = {
        'categorias_con_libros': categorias_con_libros,
        'total_categorias': categorias.count(),
        'usuarios': get_user_model().objects.all()
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
    explore_books = []

    # Get popular books from Google Books API to display
    try:
        # Search for popular/trending books across different categories
        search_queries = ['bestseller 2024', 'popular fiction', 'technology books', 'science']
        for query in search_queries:
            google_result = google_api.fetch_book_details(query)
            if isinstance(google_result, list) and google_result:
                explore_books.extend(google_result[:3])
            elif isinstance(google_result, dict) and 'books' in google_result:
                explore_books.extend(google_result['books'][:3])
            if len(explore_books) >= 12:
                break

        # Limit to 12 books
        explore_books = explore_books[:12]
    except Exception as e:
        print(f"Error fetching explore books: {e}")
        explore_books = []

    context.update({
        'user': request.user,
        'explore_books': explore_books,
        'has_explore_books': len(explore_books) > 0
    })
    return render(request, 'dashboard.html', context)


def book_search(request):
    """
    Search for books from both Google Books and Amazon.
    """
    query: QuerySet = request.GET.get('q') or request.GET.get('search', '')
    source: str     = request.GET.get('source', 'all')
    context: dict   = {
        'query'            : query,
        'google_results'   : {},
        'amazon_results'   : {},
        'combined_results' : []
    }
    
    if query:
        try:
            # Search Google Books
            if source in ['google', 'all']:
                google_result = google_api.fetch_book_details(query)

                # Check if it's an error dict or a list of books
                if isinstance(google_result, dict) and 'error' in google_result:
                    context['google_results'] = google_result
                elif isinstance(google_result, list):
                    context['google_results'] = {'books': google_result}
                    # Add Google books to combined results
                    for book in google_result:
                        combined_book = {
                            'source': 'google',
                            'title': book.get('title', 'N/A'),
                            'authors': book.get('authors', []),
                            'description': book.get('description', 'N/A'),
                            'thumbnail': book.get('thumbnail', ''),
                            'publisher': book.get('publisher', 'N/A'),
                            'published_date': book.get('publishedDate', 'N/A'),
                            'page_count': book.get('pageCount', 'N/A'),
                            'categories': book.get('categories', []),
                            'previewLink': book.get('previewLink', '#')
                        }
                        context['combined_results'].append(combined_book)
            
            # Search Amazon (fallback to sample data if API fails)
            if source in ['amazon', 'all']:
                amazon_result = amazon_api.search_books(query, max_results=5)
                context['amazon_results'] = amazon_result
                
                # Add Amazon books to combined results
                if amazon_result and 'books' in amazon_result:
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
                        context['combined_results'].append(combined_book)
                
        except Exception as e:
            print(f"Error in book search: {e}")
            context['error'] = f"Error searching books: {str(e)}"
    
    return render(request, 'book_search.html', context)

def book_search_view(request):
    """
    Book search: database first, then Google Books and Amazon APIs.
    """
    from core.api.google_books import GoogleBooksAPI
    from core.api.amazon_books import AmazonBooksAPI

    user = request.user if request.user.is_authenticated else None
    search_query = request.GET.get('search', '').strip()

    all_books = []
    db_books = []
    google_error = None
    amazon_error = None

    if search_query:
        # Search in local database first
        db_books = Libro.objects.filter(
            Q(titulo__icontains=search_query) |
            Q(autor__icontains=search_query) |
            Q(isbn__icontains=search_query)
        ).order_by('-fecha_creacion')

        for book in db_books:
            all_books.append({
                'source': 'Database',
                'book_id': book.id,
                'id': book.id,  # Also add as 'id' for template compatibility
                'title': book.titulo,
                'authors': [book.autor] if book.autor else [],
                'description': book.descripcion,
                'thumbnail': book.imagen_url if book.imagen_url else '',
                'isbn': book.isbn,
                'is_local': True,
                'book_object': book
            })

        # Search in Google Books
        try:
            google_api = GoogleBooksAPI()
            google_result = google_api.fetch_book_details(search_query)

            if isinstance(google_result, dict) and 'error' in google_result:
                google_error = google_result['error']
            elif isinstance(google_result, list):
                for book in google_result:
                    book_id = book.get('id', 'unknown')
                    all_books.append({
                        'source': 'Google Books',
                        'book_id': book_id,
                        'id': book_id,  # Also add as 'id' for template compatibility
                        'title': book.get('title', 'N/A'),
                        'authors': book.get('authors', []),
                        'description': book.get('description', 'N/A'),
                        'thumbnail': book.get('thumbnail', ''),
                        'publisher': book.get('publisher', 'N/A'),
                        'publishedDate': book.get('publishedDate', 'N/A'),
                        'pageCount': book.get('pageCount', 'N/A'),
                        'categories': book.get('categories', []),
                        'previewLink': book.get('previewLink', '#'),
                        'is_local': False
                    })
        except Exception as e:
            google_error = f"Error buscando en Google Books: {str(e)}"

        # Search in Amazon
        try:
            amazon_api = AmazonBooksAPI()
            amazon_result = amazon_api.search_books(search_query, max_results=10)

            if isinstance(amazon_result, dict) and 'error' in amazon_result:
                amazon_error = amazon_result['error']
            elif isinstance(amazon_result, dict) and 'books' in amazon_result:
                for book in amazon_result['books']:
                    book_id = book.get('asin', book.get('amazon_url', '').split('/')[-1] if 'amazon_url' in book else 'unknown')
                    all_books.append({
                        'source': 'Amazon',
                        'book_id': book_id,
                        'id': book_id,  # Also add as 'id' for template compatibility
                        'title': book.get('title', 'N/A'),
                        'authors': book.get('authors', []),
                        'description': book.get('description', 'N/A'),
                        'thumbnail': book.get('image_url', ''),
                        'price': book.get('price', 'N/A'),
                        'rating': book.get('rating', 'N/A'),
                        'amazon_url': book.get('amazon_url', ''),
                        'is_local': False
                    })
        except Exception as e:
            amazon_error = f"Error buscando en Amazon: {str(e)}"

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
    Book detail page - shows complete book information.
    Supports Google Books API, Amazon API, and local database books.
    Auto-detects if book_id is numeric (database) or string (API).
    """
    source = request.GET.get('source', None)

    if not source:
        try:
            int(book_id)
            if Libro.objects.filter(id=book_id).exists():
                source = 'database'
            else:
                source = 'google'
        except (ValueError, TypeError):
            source = 'google'

    book = None
    error = None
    availability_options = []
    
    if source == 'google':
        try:
            google_api = GoogleBooksAPI()
            book_data = google_api.get_book_by_id(book_id)

            if isinstance(book_data, dict) and 'error' in book_data:
                error = book_data['error']
            else:
                book = book_data

        except Exception as e:
            error = f'Error al cargar desde Google Books: {str(e)}'
            print(f"[DEBUG] Google Books error: {e}")
            print(f"[DEBUG] Book ID: {book_id}")
            
    elif source == 'amazon':
        try:
            amazon_api = AmazonBooksAPI()
            book_data = amazon_api.get_book_details(book_id)
            
            if isinstance(book_data, dict) and 'error' in book_data:
                error = 'No se pudo cargar la información del libro de Amazon'
            else:
                book = {
                    'title': book_data.get('title', 'N/A'),
                    'authors': book_data.get('authors', []),
                    'description': book_data.get('description', 'N/A'),
                    'thumbnail': book_data.get('image_url', ''),
                    'categories': book_data.get('categories', []),
                    'published_date': book_data.get('publication_date', 'N/A'),
                    'publishedDate': book_data.get('publication_date', 'N/A'),
                    'page_count': book_data.get('pages', 'N/A'),
                    'pageCount': book_data.get('pages', 'N/A'),
                    'publisher': book_data.get('publisher', 'N/A'),
                    'price': book_data.get('price', 'N/A'),
                    'rating': book_data.get('rating', 'N/A'),
                    'amazon_url': book_data.get('amazon_url', '#'),
                }
        except Exception as e:
            error = f'Error al cargar desde Amazon: {str(e)}'
            print(f"[DEBUG] Amazon error: {e}")
    
    elif source == 'database':
        try:
            libro = Libro.objects.get(id=book_id)
            book = {
                'title': libro.titulo,
                'authors': [libro.autor] if libro.autor else [],
                'description': libro.descripcion,
                'thumbnail': libro.imagen_url,
                'categories': [libro.categoria.nombre] if libro.categoria else [],
                'published_date': libro.fecha_publicacion.strftime('%Y-%m-%d') if libro.fecha_publicacion else None,
                'publishedDate': libro.fecha_publicacion.strftime('%Y-%m-%d') if libro.fecha_publicacion else None,
                'page_count': libro.paginas,
                'pageCount': libro.paginas,
                'publisher': 'N/A',
                'price': float(libro.precio) if libro.precio else None,
                'rating': libro.calificacion,
            }
        except Libro.DoesNotExist:
            error = 'Libro no encontrado en la base de datos'
        except Exception as e:
            error = f'Error al cargar desde base de datos: {str(e)}'
            print(f"[DEBUG] Database error: {e}")
    
    else:
        error = 'Fuente de datos no válida'

    # Build availability options
    if book and not error:
        book_title = book.get('title', '')
        book_categories = book.get('categories', [])

        # Try to find on Amazon
        if book_title:
            try:
                amazon_result = amazon_api.search_books(book_title, max_results=1)
                if isinstance(amazon_result, dict) and 'books' in amazon_result and amazon_result['books']:
                    amazon_book = amazon_result['books'][0]
                    amazon_price = amazon_book.get('price', 'Precio no disponible')
                    availability_options.append({
                        'platform': 'Amazon',
                        'platform_logo': 'amazon',
                        'price': amazon_price,
                        'language': 'Español',
                        'format': 'Físico',
                        'stock': f"{amazon_book.get('availability', 'Consultar')} disponible" if amazon_book.get('availability') else 'Consultar disponibilidad',
                        'link': amazon_book.get('amazon_url', f'https://www.amazon.com.mx/s?k={book_title.replace(" ", "+")}'),
                        'link_text': 'Ver en Amazon',
                        'show_favorite': False,
                        'rating': amazon_book.get('rating', None)
                    })
                else:
                    # Fallback Amazon option - link to search
                    availability_options.append({
                        'platform': 'Amazon',
                        'platform_logo': 'amazon',
                        'price': 'Ver precio',
                        'language': 'Español',
                        'format': 'Físico',
                        'stock': 'Consultar disponibilidad',
                        'link': f'https://www.amazon.com.mx/s?k={book_title.replace(" ", "+")}',
                        'link_text': 'Buscar en Amazon',
                        'show_favorite': False,
                        'rating': None
                    })
            except Exception as e:
                print(f"[DEBUG] Error fetching Amazon data: {e}")
                # Fallback Amazon option
                availability_options.append({
                    'platform': 'Amazon',
                    'platform_logo': 'amazon',
                    'price': 'Ver precio',
                    'language': 'Español',
                    'format': 'Físico / Digital',
                    'stock': 'Consultar disponibilidad',
                    'link': f'https://www.amazon.com.mx/s?k={book_title.replace(" ", "+")}',
                    'link_text': 'Buscar en Amazon',
                    'show_favorite': False,
                    'rating': None
                })

        # Google Books option (always available for Google source)
        if source == 'google':
            preview_link = book.get('previewLink', '')
            buy_link = book.get('buyLink', '')

            # Format price from Google Books
            google_price = None
            if book.get('price') and book.get('currency'):
                if book.get('currency') == 'USD':
                    google_price = f"${book.get('price'):.2f} USD"
                elif book.get('currency') == 'MXN':
                    google_price = f"${book.get('price'):.2f} MXN"
                else:
                    google_price = f"{book.get('price'):.2f} {book.get('currency')}"

            # Determine the best link (buy link if available, otherwise preview)
            best_link = buy_link if buy_link else preview_link
            link_text = 'Comprar en Google Books' if buy_link else 'Ver vista previa'

            # Determine stock based on saleability
            saleability = book.get('saleability', 'NOT_FOR_SALE')
            if saleability == 'FOR_SALE':
                stock_text = 'Disponible para compra'
            elif saleability == 'FREE':
                stock_text = 'Gratis'
                google_price = 'Gratis'
            else:
                stock_text = 'Solo vista previa'
                google_price = google_price or 'No disponible para compra'

            if best_link:
                availability_options.append({
                    'platform': 'Google Books',
                    'platform_logo': 'google',
                    'price': google_price,
                    'language': 'Múltiples idiomas',
                    'format': 'Digital',
                    'stock': stock_text,
                    'link': best_link,
                    'link_text': link_text,
                    'show_favorite': True,
                    'rating': None
                })

    # Get AI recommendations for related books
    related_books = []
    if book and not error:
        try:
            from core.services.ai_recommendations import AIRecommendationService

            ai_service = AIRecommendationService()
            book_title = book.get('title', '')
            book_categories = book.get('categories', [])

            # Use the first category if available, otherwise use the book title
            category_for_search = book_categories[0] if book_categories else book_title

            # Get personalized recommendations
            related_books = ai_service.get_books_by_category(
                category_name=category_for_search,
                num_books=6,
                user=request.user if request.user.is_authenticated else None
            )

            # Format related books for template
            formatted_related_books = []
            for related_book in related_books:
                formatted_related_books.append({
                    'source': 'google',
                    'id': related_book.get('id', 'unknown'),
                    'title': related_book.get('title', 'N/A'),
                    'authors': related_book.get('authors', []),
                    'thumbnail': related_book.get('thumbnail', ''),
                    'description': related_book.get('description', 'N/A'),
                })
            related_books = formatted_related_books

        except Exception as e:
            print(f"[DEBUG] Error fetching related books: {e}")
            related_books = []

    # Debug info
    print(f"[DEBUG] Source: {source}")
    print(f"[DEBUG] Book ID: {book_id}")
    print(f"[DEBUG] Book data exists: {book is not None}")
    if book:
        print(f"[DEBUG] Book title: {book.get('title', 'N/A')}")
    print(f"[DEBUG] Availability options: {len(availability_options)}")
    print(f"[DEBUG] Related books: {len(related_books)}")

    context = {
        'user': request.user,
        'book': book,
        'source': source,
        'error': error,
        'availability_options': availability_options,
        'related_books': related_books
    }

    return render(request, 'book_detail.html', context)

def categoria_detalle(request: HttpRequest, categoria_id: int) -> HttpResponse:
    """
    Muestra todos los libros de una categoría específica.
    Ahora integra IA para buscar recomendaciones en Google Books API.
    """
    from core.services.ai_recommendations import AIRecommendationService

    categoria = get_object_or_404(Categoria, id=categoria_id, activa=True)

    # Obtener parámetros de filtrado
    orden = request.GET.get('orden', '-calificacion')
    busqueda = request.GET.get('busqueda', '').strip()

    # Validar orden
    ordenes_validas = ['titulo', '-titulo', 'precio', '-precio', 'calificacion', '-calificacion']
    if orden not in ordenes_validas:
        orden = '-calificacion'

    # Obtener libros de la base de datos local
    libros_db = categoria.libros.filter(disponible=True)

    if busqueda:
        libros_db = libros_db.filter(
            Q(titulo__icontains=busqueda) |
            Q(autor__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    libros_db = libros_db.order_by(orden)

    # Obtener recomendaciones de IA + Google Books (personalizadas por usuario)
    ai_service = AIRecommendationService()
    libros_google = []
    try:
        # Pass user to get personalized recommendations
        libros_google = ai_service.get_books_by_category(
            category_name=categoria.nombre,
            num_books=12,
            user=request.user if request.user.is_authenticated else None
        )
    except Exception as e:
        print(f"Error obteniendo recomendaciones de IA para {categoria.nombre}: {e}")

    # Combinar libros de base de datos y Google Books
    all_books = []

    # Agregar libros de base de datos
    for libro in libros_db:
        all_books.append({
            'source': 'database',
            'id': libro.id,
            'title': libro.titulo,
            'authors': [libro.autor] if libro.autor else [],
            'thumbnail': libro.imagen_url,
            'description': libro.descripcion,
            'price': float(libro.precio) if libro.precio else None,
            'rating': libro.calificacion,
            'is_local': True
        })

    # Agregar libros de Google Books
    for book in libros_google:
        all_books.append({
            'source': 'google',
            'id': book.get('id', 'unknown'),
            'title': book.get('title', 'N/A'),
            'authors': book.get('authors', []),
            'thumbnail': book.get('thumbnail', ''),
            'description': book.get('description', 'N/A'),
            'publisher': book.get('publisher', 'N/A'),
            'publishedDate': book.get('publishedDate', 'N/A'),
            'pageCount': book.get('pageCount', 'N/A'),
            'categories': book.get('categories', []),
            'previewLink': book.get('previewLink', '#'),
            'is_local': False
        })

    # Estadísticas
    stats = {
        'total_libros': len(all_books),
        'libros_database': len(libros_db),
        'libros_google': len(libros_google),
        'calificacion_promedio': libros_db.aggregate(Avg('calificacion'))['calificacion__avg'] or 0,
        'precio_minimo': libros_db.aggregate(models.Min('precio'))['precio__min'] or 0,
        'precio_maximo': libros_db.aggregate(models.Max('precio'))['precio__max'] or 0,
    }

    context = {
        'categoria': categoria,
        'libros': all_books,
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


@login_required
def recomendaciones_view(request: HttpRequest) -> HttpResponse:
    """
    Recommendations view using machine learning model.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object.
    """
    engine = RecomendationEngine()
    print("Generating recommendations for user:", request.user.id)
    try:
        recommendations = engine.get_recommendations(
            user_id=request.user.id,
            top_n=12
        )
        print(recommendations)
    except Exception as e:
        print("Error generating recommendations:", e)
        recommendations = []
    return render(request, 'recomendaciones.html', {
        'recommendations' : recommendations
    })


@login_required
def api_recommendations(request):
    """API endpoint para obtener recomendaciones (JSON)"""
    engine = RecomendationEngine()
    top_n = int(request.GET.get('top_n', 10))
    
    try:
        recommendations = engine.get_recommendations(
            user_id=request.user.id,
            top_n=top_n
        )
        
        data = [{
            'id': libro.id,
            'titulo': libro.titulo,
            'autor': libro.autor,
            'precio': float(libro.precio),
            'calificacion': libro.calificacion,
            'imagen_url': libro.imagen_url,
            'categoria': libro.categoria.nombre
        } for libro in recommendations]
        
        return JsonResponse({
            'success': True,
            'recommendations': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def similar_books_view(request, libro_id):
    """Vista para mostrar libros similares a uno específico"""
    engine = RecomendationEngine()
    
    similares = engine.get_similar_books(
        libro_id=libro_id,
        top_n=6
    )
    
    return render(request, 'recomendaciones/similar_books.html', {
        'similar_books': similares
    })


@login_required
@require_http_methods(["POST"])
def agregar_favorito(request: HttpRequest, libro_id: int) -> JsonResponse:
    """
    API endpoint to add a book to user favorites.
    
    Args:
        request (HttpRequest): The HTTP request object.
        libro_id (int): The ID of the book to add to favorites.
        
    Returns:
        JsonResponse: Success or error message.
    """
    try:
        libro = get_object_or_404(Libro, id=libro_id)        
        favorito_existente = Favorito.objects.filter(
            usuario=request.user,
            libro=libro
        ).exists()
        if favorito_existente:
            return JsonResponse({
                'success': False,
                'message': 'Este libro ya está en tus favoritos'
            }, status=400)
        Favorito.objects.create(
            usuario=request.user,
            libro=libro
        )
        return JsonResponse({
            'success': True,
            'message': f'"{libro.titulo}" ha sido agregado a tus favoritos',
            'libro_id': libro_id,
            'is_favorite': True
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar a favoritos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remover_favorito(request: HttpRequest, libro_id: int) -> JsonResponse:
    """
    API endpoint to remove a book from user favorites.
    
    Args:
        request (HttpRequest): The HTTP request object.
        libro_id (int): The ID of the book to remove from favorites.
        
    Returns:
        JsonResponse: Success or error message.
    """
    try:
        libro = get_object_or_404(Libro, id=libro_id)
        favorito = Favorito.objects.filter(
            usuario=request.user,
            libro=libro
        ).first()
        if not favorito:
            return JsonResponse({
                'success': False,
                'message': 'Este libro no está en tus favoritos'
            }, status=400)
        favorito.delete()
        return JsonResponse({
            'success': True,
            'message': f'"{libro.titulo}" ha sido removido de tus favoritos',
            'libro_id': libro_id,
            'is_favorite': False
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al remover de favoritos: {str(e)}'
        }, status=500)
