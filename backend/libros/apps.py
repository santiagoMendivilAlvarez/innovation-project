"""
App configuration for the Libros application.
"""
from django.apps import AppConfig


class LibrosConfig(AppConfig):
    """
    Configuration class for the Libros application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'libros'
