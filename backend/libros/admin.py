"""
Admin configuration for the Libros application.
"""
from django.contrib import admin
from .models        import Categoria, Libro, FuenteLibro, Resena


class CategoriaAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Categoria model.
    """
    list_display  = ('nombre', 'activa')
    search_fields = ('nombre',)
    list_filter   = ('activa',)


class LibroAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Libro model.
    """
    list_display  = ('titulo', 'autor', 'isbn', 'categoria',
                      'disponible', 'calificacion')
    search_fields = ('titulo', 'autor', 'isbn')
    list_filter   = ('categoria', 'disponible')
    ordering      = ('titulo',)

class FuenteLibroAdmin(admin.ModelAdmin):
    """
    Admin configuration for the FuenteLibro model.
    """
    list_display  = ('libro', 'plataforma')
    search_fields = ('libro__titulo', 'plataforma')
    list_filter   = ('fecha_actualizacion' ,)
    ordering      = ('-fecha_actualizacion',)


class ResenaAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Resena model.
    """
    list_display  = ('libro', 'autor_resena', 'calificacion', 'fecha_creacion')
    search_fields = ('libro__titulo', 'autor_resena')
    list_filter   = ('calificacion', 'fecha_creacion')
    ordering      = ('-fecha_creacion',)


admin.site.register(FuenteLibro, FuenteLibroAdmin)
admin.site.register(Resena, ResenaAdmin)
admin.site.register(Libro, LibroAdmin)
admin.site.register(Categoria, CategoriaAdmin)
