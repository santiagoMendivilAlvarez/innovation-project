from django.urls import path
from profiles    import views


urlpatterns = [
    path('mi-biblioteca/', views.FavoritesListView.as_view(), name='mi_biblioteca'),
    path('agregar-favorito/<int:libro_id>/', views.send_to_favorites, name="agregar_favorito")
]
