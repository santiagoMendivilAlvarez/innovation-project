from django.urls import path
from profiles    import views


urlpatterns = [
    path('mi-biblioteca/', views.mi_biblioteca_view, name='mi_biblioteca'),
]
