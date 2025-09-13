"""
Admin configuration for profiles app.
"""
from django.contrib  import admin
from profiles.models import Favorito, Recomendacion, InteresUsuario


class FavoritoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Favorito model.
    """
    list_display  = ('usuario', 'libro', 'fecha_favorito')
    search_fields = ('usuario__username', 'libro__titulo')
    list_filter   = ('fecha_favorito',)
    ordering      = ('-fecha_favorito',)


class RecomendacionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Recomendacion model.
    """
    list_display  = ('usuario', 'libro', 'tipo_recomendacion',
                     'calificacion_recomendacion', 'vista', 'fecha_recomendacion')
    search_fields = ('usuario__username', 'libro__titulo', 'razon_recomendacion')
    list_filter   = ('tipo_recomendacion', 'vista', 'fecha_recomendacion')
    ordering      = ('-fecha_recomendacion',)


class InteresUsuarioAdmin(admin.ModelAdmin):
    """
    Admin configuration for the InteresUsuario model.
    """
    list_display  = ('usuario', 'categoria', 'nivel_interes')
    search_fields = ('usuario__username', 'categoria__nombre')
    list_filter   = ('nivel_interes',)
    ordering      = ('usuario__username', 'categoria__nombre')


admin.site.register(Favorito, FavoritoAdmin)
admin.site.register(Recomendacion, RecomendacionAdmin)
admin.site.register(InteresUsuario, InteresUsuarioAdmin)
