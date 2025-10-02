"""
URL configuration for libros app.
"""
from django.urls import path
from . import views

APP_NAME = 'libros'
urlpatterns = [
    path('', views.view, name='libros'),
]
