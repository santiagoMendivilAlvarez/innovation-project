"""
URL configuration for libros app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.home_view,            name='home'),
    path('libros/',                       views.books,                name="libros"),
    path('libros/buscar/',                views.book_search_view,     name='book_search'),
    path('categoria/<int:categoria_id>/', views.categoria_detalle,    name='categoria_detalle'),
    path('recomendaciones/',              views.recomendaciones_view, name='recomendaciones'),
    path('similares/<int:libro_id>/',     views.similar_books_view,   name='similar_books'),
    path("api/search/",                   views.book_search_api,      name="book_search_api"),
    path("api/recomendaciones/",          views.api_recommendations,  name='api_recommendaciones'),
    path("amazon/<str:asin>/",            views.amazon_book_details,  name="amazon_book_details"),
    path('libros/<str:book_id>/',         views.book_detail_view,     name='book_detail'),
]
