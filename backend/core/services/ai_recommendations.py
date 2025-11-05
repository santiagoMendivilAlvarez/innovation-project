"""
AI-powered book recommendations service using OpenAI
"""
import os
import json
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from core.api.google_books import GoogleBooksAPI


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', settings.SECRET_KEY))


class AIRecommendationService:
    """
    Service to generate personalized book recommendations using AI
    """

    def __init__(self):
        self.google_api = GoogleBooksAPI()

    def get_personalized_recommendations(self, user, num_books=8):
        """
        Get personalized book recommendations for a user using AI and Google Books API.

        Args:
            user: The user object
            num_books (int): Number of book recommendations to return

        Returns:
            list: List of book dictionaries with details
        """
        # Check cache first
        cache_key = f'ai_recommendations_user_{user.id}'
        cached_recommendations = cache.get(cache_key)
        if cached_recommendations:
            return cached_recommendations

        # Generate AI recommendations
        search_queries = self._generate_search_queries(user)

        # Fetch books from Google Books based on AI recommendations
        recommended_books = []
        for query in search_queries:
            try:
                books = self.google_api.fetch_book_details(query)
                if isinstance(books, list) and len(books) > 0:
                    # Add first 2 books from each query
                    for book in books[:2]:
                        if len(recommended_books) < num_books:
                            recommended_books.append(book)
            except Exception as e:
                print(f"Error fetching books for query '{query}': {e}")
                continue

        # Cache for 6 hours
        cache.set(cache_key, recommended_books, 21600)
        return recommended_books

    def _generate_search_queries(self, user):
        """
        Use OpenAI to generate personalized search queries based on user profile.

        Args:
            user: The user object

        Returns:
            list: List of search query strings
        """
        # Build user profile context
        user_context = self._build_user_context(user)

        # Create prompt for OpenAI
        system_prompt = """Eres un experto bibliotecario y recomendador de libros académicos.
Tu tarea es generar términos de búsqueda específicos para encontrar libros que sean relevantes
para un estudiante universitario basándote en su perfil académico.

IMPORTANTE:
- Genera exactamente 4 términos de búsqueda
- Los términos deben ser específicos y relacionados con su carrera
- Incluye tanto libros de texto como literatura complementaria
- Considera el nivel académico del estudiante
- Devuelve SOLO un JSON con la siguiente estructura:
{
    "search_queries": ["término1", "término2", "término3", "término4"]
}

NO incluyas explicaciones adicionales, SOLO el JSON."""

        user_prompt = f"""Perfil del estudiante:
- Nombre: {user.nombre_completo}
- Universidad: {user.get_universidad_display()}
- Carrera: {user.carrera}
- Nivel académico: {user.get_nivel_academico_display()}
- Intereses: {user.get_intereses_display()}

Genera 4 términos de búsqueda específicos para recomendar libros a este estudiante."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            # Parse the response
            response_text = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                # Remove markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                recommendations_data = json.loads(response_text)
                search_queries = recommendations_data.get('search_queries', [])

                if not search_queries:
                    # Fallback to default queries
                    return self._get_default_queries(user)

                return search_queries

            except json.JSONDecodeError:
                print(f"Error parsing AI response: {response_text}")
                return self._get_default_queries(user)

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._get_default_queries(user)

    def _build_user_context(self, user):
        """
        Build a context string from user profile.

        Args:
            user: The user object

        Returns:
            str: Formatted user context
        """
        return f"""
        Carrera: {user.carrera}
        Nivel: {user.get_nivel_academico_display()}
        Universidad: {user.get_universidad_display()}
        Intereses: {user.get_intereses_display()}
        """

    def _get_default_queries(self, user):
        """
        Get default search queries based on user's career if AI fails.

        Args:
            user: The user object

        Returns:
            list: Default search queries
        """
        career_keywords = user.carrera.lower()

        # Map common career terms to search queries
        default_queries = [
            f"{career_keywords} introducción",
            f"{career_keywords} fundamentos",
            f"libros {career_keywords}",
            f"{user.get_nivel_academico_display()} {career_keywords}"
        ]

        return default_queries

    def get_books_by_category(self, category_name, num_books=12, user=None):
        """
        Get book recommendations for a specific category using AI and Google Books API.
        Optionally personalized based on user profile.

        Args:
            category_name (str): Name of the category
            num_books (int): Number of book recommendations to return
            user: Optional user object for personalized recommendations

        Returns:
            list: List of book dictionaries with details
        """
        # NO CACHE - Always generate fresh recommendations
        # This ensures different results on each page reload

        # Generate AI search queries for this category with user context
        search_queries = self._generate_category_search_queries(category_name, user)

        # Fetch books from Google Books based on AI recommendations
        recommended_books = []
        for query in search_queries:
            try:
                books = self.google_api.fetch_book_details(query)
                if isinstance(books, list) and len(books) > 0:
                    # Add books from each query
                    for book in books[:3]:
                        if len(recommended_books) < num_books:
                            recommended_books.append(book)
            except Exception as e:
                print(f"Error fetching books for query '{query}': {e}")
                continue

        return recommended_books

    def _generate_category_search_queries(self, category_name, user=None):
        """
        Use OpenAI to generate search queries for a specific category.
        Optionally personalized based on user profile.

        Args:
            category_name (str): Name of the category
            user: Optional user object for personalization

        Returns:
            list: List of search query strings
        """
        system_prompt = """Eres un experto bibliotecario y recomendador de libros.
Tu tarea es generar términos de búsqueda específicos para encontrar los mejores libros
de una categoría específica, personalizados según el perfil del usuario.

IMPORTANTE:
- Genera exactamente 4 términos de búsqueda ÚNICOS y VARIADOS
- Los términos deben ser específicos y relevantes para la categoría
- Si hay información del usuario, personaliza las búsquedas según su carrera y nivel académico
- Incluye libros clásicos, populares, académicos y contemporáneos
- Los términos deben estar en español o inglés según sea más apropiado
- VARÍA los términos para dar RESULTADOS DIFERENTES en cada llamada
- Devuelve SOLO un JSON con la siguiente estructura:
{
    "search_queries": ["término1", "término2", "término3", "término4"]
}

NO incluyas explicaciones adicionales, SOLO el JSON."""

        # Build user context if available
        user_context = ""
        if user and hasattr(user, 'carrera'):
            user_context = f"""

Perfil del usuario:
- Carrera: {user.carrera}
- Nivel académico: {user.get_nivel_academico_display() if hasattr(user, 'get_nivel_academico_display') else 'Universitario'}
- Universidad: {user.get_universidad_display() if hasattr(user, 'get_universidad_display') else 'N/A'}

Personaliza las búsquedas considerando que el usuario estudia {user.carrera}."""

        user_prompt = f"""Categoría: {category_name}{user_context}

Genera 4 términos de búsqueda específicos y VARIADOS para encontrar los mejores libros de esta categoría.
Los libros deben ser relevantes, de calidad y apropiados para estudiantes universitarios.
IMPORTANTE: Genera búsquedas DIFERENTES cada vez que se llame, incluyendo diferentes autores, temas específicos, o enfoques."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.0,  # Higher temperature for more varied results
                max_tokens=200
            )

            # Parse the response
            response_text = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                # Remove markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                recommendations_data = json.loads(response_text)
                search_queries = recommendations_data.get('search_queries', [])

                if not search_queries:
                    # Fallback to default queries
                    return self._get_default_category_queries(category_name)

                return search_queries

            except json.JSONDecodeError:
                print(f"Error parsing AI response: {response_text}")
                return self._get_default_category_queries(category_name)

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._get_default_category_queries(category_name)

    def _get_default_category_queries(self, category_name):
        """
        Get default search queries for a category if AI fails.

        Args:
            category_name (str): Name of the category

        Returns:
            list: Default search queries
        """
        category_lower = category_name.lower()

        default_queries = [
            f"best {category_name} books",
            f"libros de {category_lower}",
            f"{category_name} bestsellers",
            f"introducción a {category_lower}"
        ]

        return default_queries
