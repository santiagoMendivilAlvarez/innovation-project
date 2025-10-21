"""
URL configuration for chatbot app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.chat_message, name='chat_message'),
    path('clear/', views.clear_chat_history, name='clear_chat_history'),
]
