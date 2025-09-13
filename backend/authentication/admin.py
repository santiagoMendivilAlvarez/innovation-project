"""
Admin configuration for the authentication app.
"""
from django.contrib        import admin
from authentication.models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    """
    Admin interface for CustomUser model.
    """
    list_display  = ('username', 'email', 'universidad', 'carrera', 'nivel_academico',
                      'email_verificado', 'suscripcion_activa', 'fecha_suscripcion',
                        'is_staff', 'is_active')
    search_fields = ('username', 'email', 'universidad', 'carrera')
    list_filter   = ('email_verificado', 'suscripcion_activa', 'is_staff', 'is_active')
    ordering      = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
