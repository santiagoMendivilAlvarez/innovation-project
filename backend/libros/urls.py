"""
URL configuration for libros app.
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.view, name='libros'),
    path("books/", views.book_search, name="book_search"),
]
