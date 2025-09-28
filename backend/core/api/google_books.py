"""
Module for interacting with the Google Books API.
"""
import requests
from django.conf       import settings
from django.http       import HttpResponse
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
        self.url: str     = GOOGLE_BOOKS_API_URL
        self.api_key: str = getattr(settings, 'GOOGLE_BOOKS_API_KEY', None) or ''


    def fetch_book_details(self: 'GoogleBooksAPI', query: str) -> dict:
        """
        Method to fetch book details with caching.
        """
        cache_key = f"google_book_{query}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        params: dict = {
            'q': f'isbn:{query}',
        }
        # Only add API key if it exists
        if self.api_key:
            params['key'] = self.api_key
            
        try:
            response = requests.get(self.url, params=params)
        except requests.RequestException as e:
            return {'error': f'Error connecting to Google Books API: {str(e)}'}

        data: dict = response.json()

        if not data.get('items'):
            data = self.__get_general_search(query, params)

        if not data.get('items'):
            result = {'error': 'No book found with the provided query.'}
        else:
            result = self.__return_results(data)

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
        response = requests.get(self.url, params=params)
        data     = response.json()
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
            'title'         : book_info.get('title', 'N/A'),
            'authors'       : book_info.get('authors', []),
            'publisher'     : book_info.get('publisher', 'N/A'),
            'publishedDate' : book_info.get('publishedDate', 'N/A'),
            'description'   : book_info.get('description', 'N/A'),
            'pageCount'     : book_info.get('pageCount', 'N/A'),
            'categories'    : book_info.get('categories', []),
            'thumbnail'     : book_info.get('imageLinks', {}).get('thumbnail', ''),
        }
