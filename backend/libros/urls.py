"""
URL configuration for libros app.
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.view, name='libros'),
]
