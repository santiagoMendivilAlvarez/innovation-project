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
import os


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', settings.SECRET_KEY))


@require_http_methods(["POST"])
@csrf_exempt  # Remove this in production and use proper CSRF handling
@login_required
def chat_message(request):
    """
    Handle chat messages and get responses from OpenAI GPT-4o-mini.
    Stores conversation history in cache.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        # Get user's conversation history from cache
        user_id = request.user.id
        cache_key = f'chat_history_{user_id}'
        conversation_history = cache.get(cache_key, [])

        # Add user message to history
        conversation_history.append({
            'role': 'user',
            'content': user_message
        })

        # Keep only last 20 messages to avoid token limits
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        # Get user information for context
        user = request.user
        user_info = f"\n\nContexto del usuario:\n- Nombre: {user.get_full_name() or user.username}\n- Email: {user.email}"

        # Get user's recent book searches or favorites if available
        try:
            from libros.models import Libro
            # Try to get user's recently viewed or searched books
            # This is just an example - adjust based on your actual models
            user_context_extra = ""
            # You can add more context here like:
            # - User's favorite genres
            # - Recently searched books
            # - User's reading preferences
        except Exception:
            user_context_extra = ""

        # System prompt for the chatbot
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
- Si el usuario busca un libro específico, pregunta detalles como género, autor o tema de interés
- Menciona que BookieWookie compara precios en Google Books y Amazon
- Si no sabes algo específico de la plataforma, sugiere al usuario explorar la sección correspondiente
{user_info}

Mantén un tono amigable, profesional y entusiasta sobre los libros. Puedes usar el nombre del usuario de manera ocasional para hacer la conversación más personal.'''
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

            # Add bot response to history
            conversation_history.append({
                'role': 'assistant',
                'content': bot_response
            })

            # Save updated history to cache (24 hours)
            cache.set(cache_key, conversation_history, 86400)

            return JsonResponse({
                'success': True,
                'message': bot_response
            })

        except Exception as openai_error:
            print(f"OpenAI API Error: {openai_error}")
            # Fallback to basic responses if OpenAI fails
            fallback_response = get_fallback_response(user_message)

            conversation_history.append({
                'role': 'assistant',
                'content': fallback_response
            })
            cache.set(cache_key, conversation_history, 86400)

            return JsonResponse({
                'success': True,
                'message': fallback_response,
                'fallback': True
            })

    except Exception as e:
        print(f"Chat Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def clear_chat_history(request):
    """Clear user's chat history from cache."""
    try:
        user_id = request.user.id
        cache_key = f'chat_history_{user_id}'
        cache.delete(cache_key)

        return JsonResponse({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_fallback_response(user_message):
    """
    Provide basic fallback responses if OpenAI API is not available.
    """
    message = user_message.lower()

    if any(word in message for word in ['hola', 'buenos', 'hey', 'hi']):
        return '''¡Hola! 👋 Bienvenido a BookieWookie.

¿En qué puedo ayudarte hoy?
🔍 Buscar libros
💰 Comparar precios
📖 Recibir recomendaciones
❓ Ayuda con la plataforma'''

    elif any(word in message for word in ['buscar', 'libro', 'encontrar']):
        return '''¡Perfecto! Te puedo ayudar a buscar libros 📚

Usa el buscador en la parte superior para encontrar libros por:
• Título
• Autor
• ISBN
• Género o tema

BookieWookie compara precios en Google Books y Amazon para darte las mejores opciones. ¿Qué libro estás buscando?'''

    elif any(word in message for word in ['recomendar', 'recomendación', 'qué leer']):
        return '''¡Me encantaría recomendarte libros! 📖✨

Para darte mejores recomendaciones, cuéntame:
🎭 ¿Qué géneros te gustan?
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
