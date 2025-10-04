"""
Module for interacting with the Google Books API.
"""
import requests
from django.conf import settings
from django.http import HttpResponse
from django.core.cache import cache
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksAPI:
    """
    API client for Google Books.
    """

    def __init__(self: 'GoogleBooksAPI') -> None:
        """
        Initialize the API client with the base URL and API key.
        """
        self.url: str = GOOGLE_BOOKS_API_URL
        self.api_key: str = getattr(
            settings, 'GOOGLE_BOOKS_API_KEY', None) or ''

    def fetch_book_details(self: 'GoogleBooksAPI', query: str) -> dict:
        """
        Method to fetch book details with caching.
        Returns a list of books or an error dict.
        Performs smart search: tries ISBN first, then general search, then related subjects.
        """
        cache_key = f"google_book_{query}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Check if API key is configured
        if not self.api_key:
            return {'error': 'Google Books API key not configured. Please add GOOGLE_BOOKS to your .env file'}

        # Try ISBN search first
        params: dict = {
            'q': f'isbn:{query}',
            'key': self.api_key,
            'maxResults': 20,
            'orderBy': 'relevance'
        }
        # Only add API key if it exists
        if self.api_key:
            params['key'] = self.api_key

        try:
            response = requests.get(self.url, params=params, timeout=5)
            response.raise_for_status()
            data: dict = response.json()
        except requests.RequestException as e:
            return {'error': f'Error connecting to Google Books API: {str(e)}'}

        # If no results with ISBN, try general search
        if not data.get('items'):
            data = self.__get_general_search(query, params)

        # If still no results, try searching by subject/category
        if not data.get('items'):
            data = self.__get_subject_search(query, params)

        if not data.get('items'):
            result = {
                'error': 'No se encontraron libros con la búsqueda proporcionada.'}
        else:
            result = self.__return_multiple_results(data)

        cache.set(cache_key, result, 86400)
        return result

    def __get_general_search(self: 'GoogleBooksAPI', query: str, params: dict) -> dict:
        """
        Method to perform a general search if ISBN search yields no results.

        Args:
            query (str): The search term for the book.
            params (dict): The parameters dictionary to be updated for general search.

        Returns:
            dict: The JSON response from the Google Books API.
        """
        params['q'] = query
        params['maxResults'] = 20
        response = requests.get(self.url, params=params)
        data = response.json()
        return data

    def __get_subject_search(self: 'GoogleBooksAPI', query: str, params: dict) -> dict:
        """
        Method to perform a subject/category search for related books.

        Args:
            query (str): The search term for the subject/category.
            params (dict): The parameters dictionary to be updated for subject search.

        Returns:
            dict: The JSON response from the Google Books API.
        """
        # Search by subject
        params['q'] = f'subject:{query}'
        params['maxResults'] = 20
        response = requests.get(self.url, params=params)
        data = response.json()

        # If still no results, try intitle search
        if not data.get('items'):
            params['q'] = f'intitle:{query}'
            response = requests.get(self.url, params=params)
            data = response.json()

        return data

    def __return_results(self: 'GoogleBooksAPI', data: dict) -> dict:
        """
        Gets the relevant book details from the API response.

        Args:
            data (dict): The JSON response from the Google Books API.

        Returns:
            dict: A dictionary containing relevant book details.
        """
        book_info = data['items'][0]['volumeInfo']
        return {
            'title': book_info.get('title', 'N/A'),
            'authors': book_info.get('authors', []),
            'publisher': book_info.get('publisher', 'N/A'),
            'publishedDate': book_info.get('publishedDate', 'N/A'),
            'description': book_info.get('description', 'N/A'),
            'pageCount': book_info.get('pageCount', 'N/A'),
            'categories': book_info.get('categories', []),
            'thumbnail': book_info.get('imageLinks', {}).get('thumbnail', ''),
        }

    def __return_multiple_results(self: 'GoogleBooksAPI', data: dict) -> list:
        """
        Gets multiple book details from the API response.

        Args:
            data (dict): The JSON response from the Google Books API.

        Returns:
            list: A list of dictionaries containing book details.
        """
        books = []
        for item in data.get('items', [])[:10]:  # Limit to 10 results
            book_info = item.get('volumeInfo', {})
            books.append({
                'title': book_info.get('title', 'N/A'),
                'authors': book_info.get('authors', []),
                'publisher': book_info.get('publisher', 'N/A'),
                'publishedDate': book_info.get('publishedDate', 'N/A'),
                'description': book_info.get('description', 'N/A')[:300] + '...' if book_info.get('description') and len(book_info.get('description', '')) > 300 else book_info.get('description', 'N/A'),
                'pageCount': book_info.get('pageCount', 'N/A'),
                'categories': book_info.get('categories', []),
                'thumbnail': book_info.get('imageLinks', {}).get('thumbnail', '').replace('http://', 'https://'),
                'previewLink': book_info.get('previewLink', '#'),
            })
        return books
