"""
URL configuration for libros app.
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.view, name='libros'),
    path("books/", views.book_search, name="book_search"),
    path("api/search/", views.book_search_api, name="book_search_api"),
    path("amazon/<str:asin>/", views.amazon_book_details, name="amazon_book_details"),
]
