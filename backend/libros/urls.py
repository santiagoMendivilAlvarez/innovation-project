"""
URL configuration for libros app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.home_view,            name='home'),
    path('libros/',                   views.books,                name="libros"),
    path("api/search/",               views.book_search_api,      name="book_search_api"),
    path("amazon/<str:asin>/",        views.amazon_book_details,  name="amazon_book_details"),
    path('libros/<str:book_id>/',     views.book_detail_view,     name='book_detail'),
    path('libros/buscar/',            views.book_search_view,     name='book_search'),
    path('recomendaciones/',          views.recomendaciones_view, name='recomendaciones'),
    path('api/recomendaciones/',      views.api_recommendations,  name='api_recommendaciones'),
    path('similares/<int:libro_id>/', views.similar_books_view,   name='similar_books'),
    path('favoritos/agregar/<int:libro_id>/', views.agregar_favorito, name='agregar_favorito'),
    path('favoritos/remover/<int:libro_id>/', views.remover_favorito, name='remover_favorito'),
]
