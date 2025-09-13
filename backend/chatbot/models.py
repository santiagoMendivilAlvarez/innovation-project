"""
Model for the Chatbot application.
"""
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class TiposEstado(models.TextChoices):
    ACTIVA   = 'activa'   , 'Activa'
    INACTIVA = 'inactiva' , 'Inactiva'
    CERRADA  = 'cerrada'  , 'Cerrada'


class ConversacionChat(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete    = models.CASCADE,
        related_name = "conversaciones_chat",
        verbose_name = "Usuario",
        help_text    = "El usuario que participa en la conversación."
    )
    titulo_conversacion = models.CharField(
        max_length   = 200,
        verbose_name = "Título de la Conversación",
        help_text    = "Ingrese el título de la conversación (máximo 200 caracteres)."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "Fecha de Creación",
        help_text    = "Fecha y hora en que se creó la conversación."
    )
    ultima_actualizacion = models.DateTimeField(
        auto_now     = True,
        verbose_name = "Última Actualización",
        help_text    = "Fecha y hora de la última actualización de la conversación."
    )
    estado = models.CharField(
        max_length   = 50,
        default      = 'activa',
        verbose_name = "Estado de la Conversación",
        help_text    = "El estado actual de la conversación.",
        choices      = TiposEstado.choices
    )


    class Meta:
        verbose_name        = "Conversación de Chat"
        verbose_name_plural = "Conversaciones de Chat"
        ordering            = ['-ultima_actualizacion']

    def __str__(self):
        return f"Conversación '{self.titulo_conversacion}' de {self.usuario.username}"


class MensajeChat(models.Model):
    conversacion = models.ForeignKey(
        ConversacionChat,
        on_delete    = models.CASCADE,
        related_name = "mensajes",
        verbose_name = "Conversación",
        help_text    = "La conversación a la que pertenece este mensaje."
    )
    tipo_mensaje = models.CharField(
        max_length   = 50,
        choices      = [('usuario', 'Usuario'), ('chatbot', 'Chatbot')],
        verbose_name = "Tipo de Mensaje",
        help_text    = "Indica si el mensaje fue enviado por el usuario o generado por el chatbot."
    )
    contenido = models.CharField(
        max_length   = 2000,
        verbose_name = "Contenido del Mensaje",
        help_text    = "Ingrese el contenido del mensaje (máximo 2000 caracteres)."
    )
    fecha_envio = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "Fecha de Envío",
        help_text    = "Fecha y hora en que se envió el mensaje."
    )
    es_del_usuario = models.BooleanField(
        default      = False,
        verbose_name = "Es del Usuario",
        help_text    = "Indica si el mensaje fue enviado por el usuario (True) o generado por el chatbot (False)."
    )

    class Meta:
        verbose_name        = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"
        ordering            = ['fecha_envio']

    def __str__(self):
        return f"Mensaje en '{self.conversacion.titulo_conversacion}' - {self.tipo_mensaje} - {self.fecha_envio}"
