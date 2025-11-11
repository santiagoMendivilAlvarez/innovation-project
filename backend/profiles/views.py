"""
Views for the profiles app.
"""
from typing import Any
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView
from profiles.models import Favorito
from libros.models import Libro


@login_required
def mi_biblioteca_view(request):
    """Vista para mostrar la biblioteca personal del usuario"""
    return render(request, 'mi_biblioteca.html')


class FavoritesListView(ListView):
    """
    List view to display all favorite books
    """
    template_name = 'mi_biblioteca.html'
    context_object_name = 'favoritos'
    model = Favorito
    paginate_by = 20
    ordering = ['-fecha_favorito']

    def get_queryset(self):
        queryset = super().get_queryset().filter(usuario=self.request.user)
        sort = self.request.GET.get('sort', 'recent')
        if sort == 'title':
            queryset = queryset.order_by('libro__titulo')
        elif sort == 'author':
            queryset = queryset.order_by('libro__autor')
        elif sort == 'rating':
            queryset = queryset.order_by('-libro__calificacion')
        else:  # recent
            queryset = queryset.order_by('-fecha_favorito')
            
        return queryset

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["total_favorites"] = self.get_queryset().count()
        return context
