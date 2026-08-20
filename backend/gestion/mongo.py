"""
Conexión a MongoDB — base de datos NO relacional del sistema.
Colecciones: notificaciones, eventos_log, analytics_cache (documentos sueltos,
sin FK reales; usuario_id/barbero_id son referencias lógicas resueltas por la app).
"""
from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_client = None


def get_mongo_client():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def get_mongo_db():
    return get_mongo_client()[settings.MONGO_DB_NAME]


def registrar_notificacion(usuario_id, tipo, mensaje, canal='interna'):
    """Inserta un documento en la colección `notificaciones`.
    No rompe el flujo principal si Mongo no está disponible: solo loguea."""
    try:
        db = get_mongo_db()
        db.notificaciones.insert_one({
            'usuario_id': usuario_id,
            'tipo': tipo,
            'mensaje': mensaje,
            'canal': canal,
            'leida': False,
            'fecha_creacion': __import__('datetime').datetime.utcnow(),
        })
    except PyMongoError:
        pass


def registrar_evento_log(usuario_id, accion, detalle=None):
    """Inserta un documento en `eventos_log` (auditoría de acciones)."""
    try:
        db = get_mongo_db()
        db.eventos_log.insert_one({
            'usuario_id': usuario_id,
            'accion': accion,
            'detalle': detalle or {},
            'fecha_creacion': __import__('datetime').datetime.utcnow(),
        })
    except PyMongoError:
        pass
