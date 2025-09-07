from django.contrib import admin
from .models import Libro

# Register your models here.

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'isbn', 'precio', 'disponible', 'fecha_creacion')
    list_filter = ('disponible', 'fecha_publicacion', 'fecha_creacion')
    search_fields = ('titulo', 'autor', 'isbn')
    list_editable = ('precio', 'disponible')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
