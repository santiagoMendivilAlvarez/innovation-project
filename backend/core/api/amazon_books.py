"""
Module for scraping Amazon Books search results.
"""
import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
import logging
import time
import re

logger = logging.getLogger(__name__)


class AmazonBooksAPI:
    """
    Web scraper for Amazon Books.
    """
    def __init__(self):
        """
        Initialize the scraper with headers to mimic a real browser.
        """
        self.base_url = "https://www.amazon.com/s"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def fetch_book_details(self, query: str, max_results: int = 10) -> dict:
        """
        Scrape Amazon for book results.
        
        Args:
            query (str): Search term for books
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Results or error message
        """
        cache_key = f"amazon_books_{query}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        params = {
            'k': query,
            'i': 'stripbooks-intl-ship',  # Books category
            's': 'relevancerank'  # Sort by relevance
        }

        try:
            # Add a small delay to be respectful to Amazon's servers
            time.sleep(0.5)
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')  # Using built-in parser
            
            # Find all book items
            books = self._parse_search_results(soup, max_results)
            
            if not books:
                result = {'error': 'No se encontraron libros en Amazon para esta búsqueda.'}
            else:
                result = books
            
            # Cache for 1 hour (Amazon prices change frequently)
            cache.set(cache_key, result, 3600)
            return result
            
        except requests.Timeout:
            logger.error(f"Timeout scraping Amazon for query: {query}")
            return {'error': 'Tiempo de espera agotado conectando con Amazon.'}
        except requests.RequestException as e:
            logger.error(f"Error scraping Amazon: {str(e)}")
            return {'error': f'Error conectando con Amazon: {str(e)}'}
        except Exception as e:
            logger.error(f"Unexpected error scraping Amazon: {str(e)}")
            return {'error': 'Error inesperado buscando en Amazon.'}

    def _parse_search_results(self, soup: BeautifulSoup, max_results: int) -> list:
        """
        Parse Amazon search results page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            max_results (int): Maximum results to return
            
        Returns:
            list: List of book dictionaries
        """
        books = []
        
        # Amazon uses different selectors, we need to try multiple patterns
        # Main search results container
        results = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for item in results[:max_results]:
            try:
                book_data = self._extract_book_data(item)
                if book_data:
                    books.append(book_data)
            except Exception as e:
                logger.warning(f"Error parsing Amazon result: {str(e)}")
                continue
        
        return books

    def _extract_book_data(self, item) -> dict:
        """
        Extract book information from a search result item.
        
        Args:
            item: BeautifulSoup element containing book data
            
        Returns:
            dict: Book information or None
        """
        try:
            # Title
            title_elem = item.find('h2')
            if not title_elem:
                return None
            title_link = title_elem.find('a')
            title = title_link.get_text(strip=True) if title_link else 'N/A'
            
            # URL
            url = 'https://www.amazon.com' + title_link.get('href', '') if title_link else '#'
            
            # Author - try multiple selectors
            author = 'N/A'
            author_elem = item.find('a', {'class': 'a-size-base'})
            if not author_elem:
                author_elem = item.find('span', {'class': 'a-size-base'})
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # Clean up author name
                author = author_text.replace('de ', '').strip()
            
            # Price
            price = 'N/A'
            price_elem = item.find('span', {'class': 'a-price'})
            if price_elem:
                price_whole = price_elem.find('span', {'class': 'a-price-whole'})
                price_fraction = price_elem.find('span', {'class': 'a-price-fraction'})
                if price_whole:
                    price = price_whole.get_text(strip=True)
                    if price_fraction:
                        price += price_fraction.get_text(strip=True)
                    price = f"${price}"
            
            # Image
            thumbnail = ''
            img_elem = item.find('img', {'class': 's-image'})
            if img_elem:
                thumbnail = img_elem.get('src', '')
            
            # Rating
            rating = 'N/A'
            rating_elem = item.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract number from "4.5 de 5 estrellas"
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    rating = match.group(1)
            
            # Reviews count
            reviews = 'N/A'
            reviews_elem = item.find('span', {'class': 'a-size-base', 'dir': 'auto'})
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                # Extract number
                match = re.search(r'([\d,]+)', reviews_text)
                if match:
                    reviews = match.group(1)
            
            # Format
            format_type = 'Libro'
            format_elem = item.find('a', {'class': 'a-size-base a-link-normal s-underline-text'})
            if format_elem:
                format_type = format_elem.get_text(strip=True)
            
            return {
                'title': title,
                'authors': [author] if author != 'N/A' else [],
                'price': price,
                'thumbnail': thumbnail,
                'url': url,
                'rating': rating,
                'reviews': reviews,
                'format': format_type,
                'source': 'Amazon'
            }
            
        except Exception as e:
            logger.warning(f"Error extracting book data: {str(e)}")
            return None

