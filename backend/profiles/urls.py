from django.urls import path
from profiles import views

urlpatterns = [
    path('', views.perfil_view, name='perfil'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('configuracion/editar-perfil/', views.editar_perfil_view, name='editar_perfil'),
    path('configuracion/cambiar-email/', views.cambiar_email, name='cambia_email'),
    path('configuracion/verificar-nuevo-email/', views.verificar_nuevo_email, name='verificar_nuevo_email'),
    path('configuracion/cambiar-contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('configuracion/editar-intereses/', views.editar_intereses, name='editar_intereses'),
    path('mi-biblioteca/', views.mi_biblioteca_view, name='mi_biblioteca'),
]