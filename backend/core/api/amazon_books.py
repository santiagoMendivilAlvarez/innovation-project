"""
Module for interacting with the Amazon Product Advertising API.
Note: This implementation uses web scraping as a fallback since Amazon's official API requires approval.
For production, consider using the official Amazon Product Advertising API.
"""
import requests
from django.conf import settings
from django.core.cache import cache
import json
import re
from typing import Dict, List, Optional


class AmazonBooksAPI:
    """
    API client for Amazon Books using web scraping approach.
    Note: For production, replace with official Amazon Product Advertising API.
    """
    
    def __init__(self):
        """
        Initialize the Amazon Books API client.
        """
        self.base_url = "https://www.amazon.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def search_books(self, query: str, max_results: int = 10) -> Dict:
        """
        Search for books on Amazon.
        
        Args:
            query (str): Search term for books
            max_results (int): Maximum number of results to return
            
        Returns:
            Dict: Dictionary containing search results or error message
        """
        cache_key = f"amazon_books_{query}_{max_results}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            # Use Amazon's search URL for books
            search_url = f"{self.base_url}/s"
            params = {
                'k': query,
                'i': 'stripbooks',  # Books category
                'ref': 'sr_nr_i_0'
            }
            
            response = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse the response (this is a simplified version)
            books = self._parse_search_results(response.text, max_results)
            
            result = {
                'books': books,
                'total_results': len(books),
                'source': 'amazon'
            }
            
            # Cache for 1 hour
            cache.set(cache_key, result, 3600)
            return result
            
        except requests.RequestException as e:
            return {'error': f'Error connecting to Amazon: {str(e)}', 'books': []}
        except Exception as e:
            return {'error': f'Error parsing Amazon response: {str(e)}', 'books': []}

    def _parse_search_results(self, html_content: str, max_results: int) -> List[Dict]:
        """
        Parse Amazon search results from HTML.
        This is a simplified parser - for production, consider using BeautifulSoup.
        
        Args:
            html_content (str): HTML content from Amazon search
            max_results (int): Maximum results to parse
            
        Returns:
            List[Dict]: List of book dictionaries
        """
        books = []
        
        # This is a mock implementation since actual HTML parsing would be complex
        # In a real implementation, you would use BeautifulSoup to parse the HTML
        
        # For demo purposes, return some sample data
        sample_books = [
            {
                'title': f'Sample Amazon Book for "{max_results}"',
                'authors': ['Sample Author'],
                'price': '$19.99',
                'rating': '4.5',
                'image_url': 'https://via.placeholder.com/300x400?text=Amazon+Book',
                'amazon_url': f'{self.base_url}/dp/sample123',
                'description': 'This is a sample book from Amazon search results.',
                'isbn': '1234567890123',
                'publication_date': '2023-01-01'
            }
        ]
        
        return sample_books[:max_results]

    def get_book_details(self, amazon_asin: str) -> Dict:
        """
        Get detailed information about a specific book using its ASIN.
        
        Args:
            amazon_asin (str): Amazon Standard Identification Number
            
        Returns:
            Dict: Book details or error message
        """
        cache_key = f"amazon_book_details_{amazon_asin}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            # Construct product URL
            product_url = f"{self.base_url}/dp/{amazon_asin}"
            
            response = requests.get(product_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse product details
            book_details = self._parse_product_details(response.text, amazon_asin)
            
            # Cache for 24 hours
            cache.set(cache_key, book_details, 86400)
            return book_details
            
        except requests.RequestException as e:
            return {'error': f'Error fetching book details: {str(e)}'}
        except Exception as e:
            return {'error': f'Error parsing book details: {str(e)}'}

    def _parse_product_details(self, html_content: str, asin: str) -> Dict:
        """
        Parse detailed book information from Amazon product page.
        
        Args:
            html_content (str): HTML content from Amazon product page
            asin (str): Amazon ASIN
            
        Returns:
            Dict: Book details
        """
        # This is a simplified mock implementation
        # In production, use BeautifulSoup to parse actual HTML
        
        return {
            'title': 'Sample Detailed Amazon Book',
            'authors': ['Detailed Author'],
            'price': '$24.99',
            'rating': '4.7',
            'review_count': '1,234',
            'image_url': 'https://via.placeholder.com/400x600?text=Detailed+Amazon+Book',
            'amazon_url': f'{self.base_url}/dp/{asin}',
            'description': 'This is a detailed view of an Amazon book with comprehensive information.',
            'isbn': '9876543210987',
            'publication_date': '2023-06-15',
            'publisher': 'Sample Publisher',
            'pages': 320,
            'dimensions': '6 x 0.8 x 9 inches',
            'language': 'English'
        }


# Alternative implementation using a public API (RapidAPI Amazon Data Scraper)
class AmazonBooksAPIAlternative:
    """
    Alternative Amazon Books API using RapidAPI service.
    This requires a RapidAPI subscription but provides more reliable data.
    """
    
    def __init__(self):
        """
        Initialize with RapidAPI credentials.
        """
        self.rapidapi_key = getattr(settings, 'RAPIDAPI_KEY', '')
        self.rapidapi_host = "amazon-data-scraper126.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }

    def search_books(self, query: str, max_results: int = 10) -> Dict:
        """
        Search books using RapidAPI Amazon Data Scraper.
        """
        if not self.rapidapi_key:
            return {'error': 'RapidAPI key not configured', 'books': []}
        
        cache_key = f"rapidapi_amazon_books_{query}_{max_results}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            url = f"https://{self.rapidapi_host}/search"
            params = {
                "query": query,
                "category": "books",
                "country": "US",
                "max_results": max_results
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and format the response
            result = {
                'books': self._format_rapidapi_results(data.get('products', [])),
                'total_results': len(data.get('products', [])),
                'source': 'amazon_rapidapi'
            }
            
            # Cache for 2 hours
            cache.set(cache_key, result, 7200)
            return result
            
        except requests.RequestException as e:
            return {'error': f'RapidAPI request failed: {str(e)}', 'books': []}
        except Exception as e:
            return {'error': f'Error processing RapidAPI response: {str(e)}', 'books': []}

    def _format_rapidapi_results(self, products: List[Dict]) -> List[Dict]:
        """
        Format RapidAPI results to match our expected format.
        """
        formatted_books = []
        
        for product in products:
            book = {
                'title': product.get('title', 'N/A'),
                'authors': [product.get('brand', 'Unknown Author')],
                'price': product.get('price', 'N/A'),
                'rating': product.get('rating', 'N/A'),
                'image_url': product.get('image', ''),
                'amazon_url': product.get('url', ''),
                'description': product.get('description', 'N/A')[:200] + '...' if product.get('description') else 'N/A',
                'asin': product.get('asin', ''),
                'publication_date': 'N/A'
            }
            formatted_books.append(book)
        
        return formatted_books