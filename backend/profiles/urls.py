from django.urls import path
from profiles    import views


urlpatterns = [
    path('mi-biblioteca/', views.FavoritesListView.as_view(), name='mi_biblioteca'),
]
