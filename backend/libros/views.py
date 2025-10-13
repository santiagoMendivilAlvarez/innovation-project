"""
Views for the libros app.
"""
from django.shortcuts               import render, redirect
from django.contrib.auth            import get_user_model
from .models                        import Libro
from django.http                    import HttpResponse, JsonResponse, HttpRequest
from django.views.decorators.http   import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models               import QuerySet
from libros.models                  import Libro
from core.api.google_books          import GoogleBooksAPI
from core.api.amazon_books          import AmazonBooksAPI, AmazonBooksAPIAlternative
google_api      = GoogleBooksAPI()
amazon_api      = AmazonBooksAPI()
amazon_rapidapi = AmazonBooksAPIAlternative()


def books(request: HttpRequest) -> HttpResponse:
    """
    Display all books.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered response containing all books and users.
    """
    context: dict = {
        'libros'  : Libro.objects.all(),
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
    if request.user.is_authenticated:
        user           = request.user
        intereses_list = user.get_intereses_list()
        search_query   = request.GET.get('search', '').strip()
        if search_query:
            return redirect(f'book_search?search={search_query}') # @todo: This must search the books in another view.
        context = {
            'user'             : user,
            'intereses'        : intereses_list,
            'intereses_display': user.get_intereses_display(),
            'total_intereses'  : len(intereses_list),
            'email_verified'   : user.email_verificado,
        }

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
                context['google_results'] = google_result
                
                # Add Google book to combined results if found
                if google_result and 'error' not in google_result and google_result.get('title', 'N/A') != 'N/A':
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