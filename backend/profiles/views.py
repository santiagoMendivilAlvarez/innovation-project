"""
Views for the profiles app.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def mi_biblioteca_view(request):
    """Vista para mostrar la biblioteca personal del usuario"""
    return render(request, 'mi_biblioteca.html')