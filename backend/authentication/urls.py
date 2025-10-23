"""
URLs for authentication app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('confirm_email/', views.confirm_email_view, name='confirm_email'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code_view,
         name='verify_reset_code'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('api/send-verification-code/', views.send_verification_code,
          name='send_verification_code'),
    path('api/user-data/', views.user_data_api, name='user_data_api'),
    path('api/update-intereses/', views.update_intereses_api, name='update_intereses_api'),
]
