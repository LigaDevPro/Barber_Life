from datetime import timezone as dt_timezone

from bson import ObjectId
from bson.errors import InvalidId
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..mongo import get_mongo_db
from ..serializers import NotificacionSerializer

# ---------------------------------------------------------------------------
# Notificaciones — colección Mongo `notificaciones` (gestion/mongo.py), no
# un modelo Django. Cada usuario ve solo las propias (usuario_id).
# ---------------------------------------------------------------------------

PAGE_SIZE_DEFAULT = 7


def _serializar(doc):
    fecha = doc.get('fecha_creacion')
    # mongo.py guarda datetime.utcnow() (naive). Con USE_TZ=True, DRF
    # interpretaría un naive como si ya estuviera en la timezone local
    # (America/Argentina/Cordoba) en vez de UTC, corriendo la hora mostrada
    # 3hs para adelante — acá le marcamos explícitamente que es UTC antes
    # de que llegue al serializer.
    if fecha is not None and fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=dt_timezone.utc)
    return {
        'id': str(doc['_id']),
        'tipo': doc.get('tipo', ''),
        'mensaje': doc.get('mensaje', ''),
        'canal': doc.get('canal', 'interna'),
        'leida': doc.get('leida', False),
        'fecha_creacion': fecha,
    }


def _parse_entero_positivo(valor, default):
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


class NotificacionListView(APIView):
    """GET /api/notificaciones/?leida=true|false&page=&page_size= — propias,
    más nuevas primero. Pagina a nivel de Mongo (skip/limit), no en Python:
    con `PaginacionEstandar` (pensada para querysets de Django) hubiera
    traído la colección entera a memoria antes de recortar la página."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        filtro = {'usuario_id': request.user.id}
        leida_param = request.query_params.get('leida')
        if leida_param is not None:
            valor = leida_param.lower()
            if valor not in ('true', 'false'):
                raise ValidationError({'leida': "Tiene que ser 'true' o 'false'."})
            filtro['leida'] = valor == 'true'

        page = _parse_entero_positivo(request.query_params.get('page'), 1)
        page_size = _parse_entero_positivo(request.query_params.get('page_size'), PAGE_SIZE_DEFAULT)

        coleccion = get_mongo_db().notificaciones
        count = coleccion.count_documents(filtro)
        num_pages = max(1, -(-count // page_size))  # ceil(count / page_size)

        docs = (
            coleccion.find(filtro)
            .sort('fecha_creacion', -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        data = [_serializar(d) for d in docs]
        serializer = NotificacionSerializer(data, many=True)

        return Response({
            'count': count,
            'page': page,
            'num_pages': num_pages,
            'results': serializer.data,
        })


class NotificacionLeidaView(APIView):
    """PATCH /api/notificaciones/<id>/leida/ — marca una notificación propia
    como leída. `id` es el ObjectId de Mongo, no un pk numérico."""
    permission_classes = (IsAuthenticated,)

    def patch(self, request, id):
        try:
            object_id = ObjectId(id)
        except (InvalidId, TypeError):
            raise NotFound('Notificación no encontrada.')

        db = get_mongo_db()
        doc = db.notificaciones.find_one({'_id': object_id})
        if doc is None or doc.get('usuario_id') != request.user.id:
            raise NotFound('Notificación no encontrada.')

        db.notificaciones.update_one({'_id': object_id}, {'$set': {'leida': True}})
        doc['leida'] = True
        return Response(NotificacionSerializer(_serializar(doc)).data)
