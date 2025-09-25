"""
Views for the libros app.
"""
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from libros.models import Libro
from core.api.google_books import GoogleBooksAPI
from core.api.amazon_books import AmazonBooksAPI, AmazonBooksAPIAlternative
import json

google_api = GoogleBooksAPI()
amazon_api = AmazonBooksAPI()
amazon_rapidapi = AmazonBooksAPIAlternative()


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
    """
    Search for books from both Google Books and Amazon.
    """
    query = request.GET.get('q', '')
    source = request.GET.get('source', 'all')  # 'google', 'amazon', or 'all'
    
    google_results = {}
    amazon_results = {}
    
    if query:
        if source in ['google', 'all']:
            google_results = google_api.fetch_book_details(query)
        
        if source in ['amazon', 'all']:
            amazon_results = amazon_api.search_books(query, max_results=5)
    
    context = {
        'google_results': google_results,
        'amazon_results': amazon_results,
        'query': query,
        'source': source
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
