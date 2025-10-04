"""
URLs for authentication app.
"""
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('recomendaciones/', views.recomendaciones_view, name='recomendaciones'),
    path('mi-biblioteca/', views.mi_biblioteca_view, name='mi_biblioteca'),
    path('confirm_email/', views.confirm_email_view, name='confirm_email'),

    # Password reset
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code_view, name='verify_reset_code'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    #API endpoints
    path('api/send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('api/user-data/', views.user_data_api, name='user_data_api'),
    path('api/update-intereses/', views.update_intereses_api, name='update_intereses_api'),
    path('libros/', include("libros.urls")),
]