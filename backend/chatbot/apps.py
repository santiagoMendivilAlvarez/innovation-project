"""
Application configuration for the chatbot app.
"""
from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    """
    App configuration for the chatbot app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
