from rest_framework import serializers


class NotificacionSerializer(serializers.Serializer):
    """No está atado a un modelo Django: los documentos vienen de Mongo
    (colección `notificaciones`, ver gestion/mongo.py). `id` es el ObjectId
    convertido a string por la vista antes de llegar acá."""
    id = serializers.CharField()
    tipo = serializers.CharField()
    mensaje = serializers.CharField()
    canal = serializers.CharField()
    leida = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
