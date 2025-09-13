"""
Admin configuration for the authentication app.
"""
from django.contrib import admin
from chatbot.models import MensajeChat, ConversacionChat


class MensajeChatAdmin(admin.ModelAdmin):
    """
    Admin interface for MensajeChat model.
    """
    list_display  = ('conversacion', 'tipo_mensaje', 'contenido', 'es_del_usuario', 'fecha_envio')
    search_fields = ('tipo_mensaje', 'contenido')
    list_filter   = ('es_del_usuario', 'fecha_envio')
    ordering      = ('-fecha_envio',)

class ConversacionChatAdmin(admin.ModelAdmin):
    """
    Admin interface for ConversacionChat model.
    """
    list_display  = ('usuario', 'titulo_conversacion', 'estado', 'fecha_creacion', 'ultima_actualizacion')
    search_fields = ('titulo_conversacion', 'usuario__username', 'usuario__email')
    list_filter   = ('estado', 'fecha_creacion', 'ultima_actualizacion')
    ordering      = ('-fecha_creacion',)


admin.site.register(MensajeChat     , MensajeChatAdmin)
admin.site.register(ConversacionChat, ConversacionChatAdmin)
