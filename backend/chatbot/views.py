"""
Views for the Chatbot application.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from openai import OpenAI
from django.conf import settings
from django.urls import reverse
from .models import ConversacionChat, MensajeChat
import os
import re


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', settings.SECRET_KEY))


@require_http_methods(["POST"])
@csrf_exempt  # Remove this in production and use proper CSRF handling
@login_required
def chat_message(request):
    """
    Handle chat messages and get responses from OpenAI GPT-4o-mini.
    Stores conversation history in database and cache.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        user = request.user

        # Get or create active conversation for user
        conversacion, created = ConversacionChat.objects.get_or_create(
            usuario=user,
            estado='activa',
            defaults={
                'titulo_conversacion': user_message[:50] + '...' if len(user_message) > 50 else user_message
            }
        )

        # Save user message to database
        MensajeChat.objects.create(
            conversacion=conversacion,
            tipo_mensaje='usuario',
            contenido=user_message,
            es_del_usuario=True
        )

        # Get conversation history from database (last 20 messages)
        mensajes_db = MensajeChat.objects.filter(
            conversacion=conversacion
        ).order_by('-fecha_envio')[:20]

        # Reverse to get chronological order and build conversation history
        conversation_history = []
        for msg in reversed(mensajes_db):
            role = 'user' if msg.es_del_usuario else 'assistant'
            conversation_history.append({
                'role': role,
                'content': msg.contenido
            })

        # Get user information for context
        user_info = f"\n\nContexto del usuario:\n- Nombre: {user.get_full_name() or user.username}\n- Email: {user.email}"

        # System prompt for the chatbot with search capabilities
        system_message = {
            'role': 'system',
            'content': f'''Eres un asistente virtual amigable y útil de BookieWookie, una plataforma de búsqueda y comparación de libros.

Tu rol es ayudar a los usuarios a:
- Encontrar libros por título, autor, género o tema
- Recomendar libros según sus preferencias
- Explicar cómo usar la plataforma
- Responder preguntas sobre libros en general

Características importantes:
- Sé conciso pero informativo
- Usa emojis apropiados para hacer la conversación más amigable
- Menciona que BookieWookie compara precios en Google Books y Amazon
{user_info}

**IMPORTANTE - Búsquedas de libros:**
Cuando el usuario mencione un libro específico, categoría o género que quiera buscar, DEBES incluir en tu respuesta un enlace de búsqueda usando este formato EXACTO:
[SEARCH:término de búsqueda]

Ejemplos:
- Si dice "Busco libros de Harry Potter" → incluye [SEARCH:Harry Potter]
- Si dice "Quiero libros de ciencia ficción" → incluye [SEARCH:ciencia ficción]
- Si dice "Libros de Gabriel García Márquez" → incluye [SEARCH:Gabriel García Márquez]
- Si dice "El principito" → incluye [SEARCH:El principito]

Puedes incluir el enlace en una frase natural, por ejemplo:
"¡Claro! Te ayudo a buscar [SEARCH:Harry Potter]. BookieWookie compara precios..."

Mantén un tono amigable, profesional y entusiasta sobre los libros.'''
        }

        # Prepare messages for OpenAI API
        messages = [system_message] + conversation_history

        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            bot_response = response.choices[0].message.content

            # Process search links in response
            bot_response_with_links = process_search_links(bot_response)

            # Save bot response to database
            MensajeChat.objects.create(
                conversacion=conversacion,
                tipo_mensaje='chatbot',
                contenido=bot_response_with_links,
                es_del_usuario=False
            )

            return JsonResponse({
                'success': True,
                'message': bot_response_with_links
            })

        except Exception as openai_error:
            print(f"OpenAI API Error: {openai_error}")
            # Fallback to basic responses if OpenAI fails
            fallback_response = get_fallback_response(user_message)
            fallback_response = process_search_links(fallback_response)

            # Save fallback response to database
            MensajeChat.objects.create(
                conversacion=conversacion,
                tipo_mensaje='chatbot',
                contenido=fallback_response,
                es_del_usuario=False
            )

            return JsonResponse({
                'success': True,
                'message': fallback_response,
                'fallback': True
            })

    except Exception as e:
        print(f"Chat Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def process_search_links(text):
    """
    Convert [SEARCH:query] tags to actual HTML links.
    """
    def replace_search(match):
        query = match.group(1)
        # Create the search URL - using the correct URL pattern
        search_url = f"/libros/buscar/?search={query}"
        return f'<a href="{search_url}" class="chat-search-link" target="_blank">🔍 Buscar: {query}</a>'

    # Replace all [SEARCH:query] with clickable links
    processed = re.sub(r'\[SEARCH:(.*?)\]', replace_search, text)
    return processed


@require_http_methods(["GET"])
@login_required
def get_chat_history(request):
    """Get user's active chat conversation history."""
    try:
        user = request.user

        # Get active conversation
        conversacion = ConversacionChat.objects.filter(
            usuario=user,
            estado='activa'
        ).first()

        if not conversacion:
            return JsonResponse({'success': True, 'messages': []})

        # Get all messages from the conversation
        mensajes = MensajeChat.objects.filter(
            conversacion=conversacion
        ).order_by('fecha_envio')

        messages_list = []
        for msg in mensajes:
            messages_list.append({
                'content': msg.contenido,
                'isUser': msg.es_del_usuario,
                'timestamp': msg.fecha_envio.isoformat()
            })

        return JsonResponse({
            'success': True,
            'messages': messages_list
        })
    except Exception as e:
        print(f"Get history error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def clear_chat_history(request):
    """Clear user's active chat conversation from database."""
    try:
        user = request.user

        # Get active conversation
        conversacion = ConversacionChat.objects.filter(
            usuario=user,
            estado='activa'
        ).first()

        if conversacion:
            # Mark conversation as closed instead of deleting
            conversacion.estado = 'cerrada'
            conversacion.save()

        # Clear cache as well
        cache_key = f'chat_history_{user.id}'
        cache.delete(cache_key)

        return JsonResponse({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_fallback_response(user_message):
    """
    Provide basic fallback responses if OpenAI API is not available.
    Includes search link detection.
    """
    message = user_message.lower()

    # Try to detect specific book searches
    search_keywords = extract_search_query(user_message)

    if any(word in message for word in ['hola', 'buenos', 'hey', 'hi']):
        return '''¡Hola! 👋 Bienvenido a BookieWookie.

¿En qué puedo ayudarte hoy?
🔍 Buscar libros
💰 Comparar precios
📖 Recibir recomendaciones
❓ Ayuda con la plataforma'''

    elif search_keywords:
        return f'''¡Perfecto! Te ayudo a buscar "{search_keywords}" 📚

[SEARCH:{search_keywords}]

BookieWookie compara precios en Google Books y Amazon para darte las mejores opciones.'''

    elif any(word in message for word in ['buscar', 'libro', 'encontrar']):
        return '''¡Perfecto! Te puedo ayudar a buscar libros 📚

Usa el buscador en la parte superior para encontrar libros por:
• Título
• Autor
• ISBN
• Género o tema

BookieWookie compara precios en Google Books y Amazon para darte las mejores opciones. ¿Qué libro estás buscando?'''

    elif any(word in message for word in ['recomendar', 'recomendación', 'qué leer', 'ficción', 'romance', 'misterio', 'terror', 'fantasía']):
        # Detect if they mentioned a specific genre
        genres = {
            'ficción': 'ficción',
            'romance': 'romance',
            'misterio': 'misterio',
            'terror': 'terror',
            'fantasía': 'fantasía',
            'ciencia ficción': 'ciencia ficción',
            'autobiografía': 'autobiografía',
            'historia': 'historia'
        }

        detected_genre = None
        for genre_key, genre_value in genres.items():
            if genre_key in message:
                detected_genre = genre_value
                break

        if detected_genre:
            return f'''¡Excelente elección! Te ayudo a encontrar libros de {detected_genre} 📖

[SEARCH:{detected_genre}]

¿Hay algún autor o libro específico de este género que te interese?'''
        else:
            return '''¡Me encantaría recomendarte libros! 📖✨

Para darte mejores recomendaciones, cuéntame:
🎭 ¿Qué géneros te gustan? (ficción, romance, misterio, etc.)
👤 ¿Tienes autores favoritos?
📚 ¿Qué fue lo último que leíste y te gustó?

¡Mientras más me cuentes, mejor será mi recomendación!'''

    elif any(word in message for word in ['precio', 'costo', 'barato']):
        return '''💰 ¡BookieWookie compara precios automáticamente!

Cuando buscas un libro, te mostramos:
✅ Precios en Google Books
✅ Precios en Amazon
✅ Enlaces directos para comprar

Así siempre obtienes el mejor precio disponible. ¿Qué libro estás buscando?'''

    elif any(word in message for word in ['ayuda', 'cómo', 'funciona']):
        return '''¡Te explico cómo usar BookieWookie! 🎯

**Búsqueda:**
🔍 Usa el buscador arriba para encontrar cualquier libro

**Comparación:**
💰 Ve precios de múltiples tiendas al instante

**Detalles:**
📚 Información completa: sinopsis, autor, reseñas

**Biblioteca:**
📖 Guarda tus libros favoritos

¿Hay algo específico que quieras saber?'''

    else:
        return '''Estoy aquí para ayudarte con BookieWookie 🤖

Puedo ayudarte a:
🔍 Buscar libros específicos
💰 Comparar precios
📖 Recomendar lecturas
❓ Resolver dudas sobre la plataforma

¿En qué te puedo ayudar?'''


def extract_search_query(user_message):
    """
    Extract potential book search queries from user message.
    Returns the search term or None if not detected.
    """
    message = user_message.lower()

    # Common patterns for book searches
    patterns = [
        r'busco?\s+(?:el\s+libro\s+)?["\']?([^"\']+?)["\']?(?:\s+por|\s+de|$)',
        r'quiero\s+(?:leer\s+)?["\']?([^"\']+?)["\']?(?:\s+por|\s+de|$)',
        r'me\s+interesa\s+["\']?([^"\']+?)["\']?(?:\s+por|\s+de|$)',
        r'libros?\s+(?:de|sobre)\s+["\']?([^"\']+?)["\']?(?:\s+por|$)',
        r'autor\s+["\']?([^"\']+?)["\']?$',
        r'["\']([^"\']{3,})["\']',  # Anything in quotes
    ]

    # Try to match patterns
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            query = match.group(1).strip()
            # Filter out common stop words
            if len(query) > 2 and query not in ['de', 'el', 'la', 'los', 'las', 'un', 'una', 'por']:
                return query

    # Check for book titles mentioned directly (common books)
    common_books = [
        'harry potter', 'cien años de soledad', 'el principito',
        'don quijote', 'cronwell', 'el código da vinci',
        'los juegos del hambre', 'crepúsculo', '1984',
        'orgullo y prejuicio', 'el hobbit', 'el señor de los anillos'
    ]

    for book in common_books:
        if book in message:
            return book

    return None
