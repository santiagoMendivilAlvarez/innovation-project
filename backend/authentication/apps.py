"""
Application configuration for the authentication app.
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    App configuration for the authentication app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
