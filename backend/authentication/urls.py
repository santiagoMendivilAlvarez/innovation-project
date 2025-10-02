"""
URLs for authentication app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('libros/buscar/', views.book_search_view, name='book_search'),
    path('libros/<str:book_id>/', views.book_detail_view, name='book_detail'),
    
    path('confirm_email/', views.confirm_email_view, name='confirm_email'),
    
    path('api/send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('api/user-data/', views.user_data_api, name='user_data_api'),
    path('api/update-intereses/', views.update_intereses_api, name='update_intereses_api'),
]