from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Servicio, Horario, BarberoServicio
from ..permissions import EsAdministrador, EsBarberoOAdmin
from ..serializers import ServicioSerializer, HorarioSerializer, BarberoServicioSerializer

# ---------------------------------------------------------------------------
# Catálogo y disponibilidad: Servicio, Horario, BarberoServicio.
# ---------------------------------------------------------------------------


def _es_admin(usuario):
    return bool(usuario and usuario.is_authenticated and usuario.rol == 'admin')


class SoftDeleteMixin:
    """DELETE no borra la fila: solo pone `activo=False`. Los recursos del
    catálogo tienen FKs con on_delete=PROTECT/CASCADE que no queremos
    disparar con un borrado real (Turnos ya hechos, horarios dependientes)."""

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=['activo'])


class ServicioListCreateView(generics.ListCreateAPIView):
    """GET /api/servicios/ — catálogo público (solo activos, salvo admin).
    POST /api/servicios/ — alta, solo Admin."""
    serializer_class = ServicioSerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsAdministrador()]
        return [AllowAny()]

    def get_queryset(self):
        qs = Servicio.objects.all().order_by('nombre')
        if not _es_admin(self.request.user):
            qs = qs.filter(activo=True)
        return qs


class ServicioDetailView(SoftDeleteMixin, generics.RetrieveUpdateDestroyAPIView):
    """GET público (solo activos, salvo admin). PATCH/DELETE solo Admin.
    DELETE es soft delete: hay Turnos con on_delete=PROTECT hacia Servicio."""
    serializer_class = ServicioSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD'):
            return [AllowAny()]
        return [IsAuthenticated(), EsAdministrador()]

    def get_queryset(self):
        qs = Servicio.objects.all()
        if not _es_admin(self.request.user):
            qs = qs.filter(activo=True)
        return qs


class HorarioListCreateView(generics.ListCreateAPIView):
    """GET /api/horarios/?barbero=<id> — el barbero ve los propios, el admin
    ve todos (filtrable). POST — el barbero solo puede crear para sí mismo;
    el admin puede indicar cualquier `barbero` en el body."""
    serializer_class = HorarioSerializer
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)
    pagination_class = None

    def get_queryset(self):
        usuario = self.request.user
        qs = Horario.objects.select_related('barbero__usuario')
        if _es_admin(usuario):
            barbero_id = self.request.query_params.get('barbero')
            if barbero_id:
                qs = qs.filter(barbero_id=barbero_id)
        else:
            barbero = getattr(usuario, 'barbero', None)
            qs = qs.filter(barbero=barbero) if barbero else qs.none()
        return qs.order_by('dia_semana', 'hora_inicio')

    def perform_create(self, serializer):
        usuario = self.request.user
        if _es_admin(usuario):
            if serializer.validated_data.get('barbero') is None:
                raise ValidationError({'barbero': 'Este campo es obligatorio.'})
            serializer.save()
            return
        barbero = getattr(usuario, 'barbero', None)
        if barbero is None:
            raise PermissionDenied('Tu usuario no tiene un perfil de Barbero asociado.')
        serializer.save(barbero=barbero)


class HorarioDetailView(SoftDeleteMixin, generics.RetrieveUpdateDestroyAPIView):
    """Dueño (barbero) o Admin. DELETE es soft delete (activo=False): un
    borrado real arrastraría por CASCADE los BarberoServicio de ese horario."""
    serializer_class = HorarioSerializer
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)
    queryset = Horario.objects.select_related('barbero__usuario')

    def get_object(self):
        obj = super().get_object()
        usuario = self.request.user
        if not _es_admin(usuario):
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None or obj.barbero_id != barbero.id:
                raise PermissionDenied('No podés modificar horarios de otro barbero.')
        return obj


class BarberoServicioListCreateView(generics.ListCreateAPIView):
    """GET /api/barbero-servicio/?barbero=<id> — público (arma el flujo de
    reserva). POST — el barbero arma su propia oferta; el admin puede armarla
    para cualquiera. El horario indicado tiene que ser de ese mismo barbero."""
    serializer_class = BarberoServicioSerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), EsBarberoOAdmin()]
        return [AllowAny()]

    def get_queryset(self):
        qs = BarberoServicio.objects.filter(activo=True).select_related(
            'barbero__usuario', 'servicio', 'horario',
        )
        barbero_id = self.request.query_params.get('barbero')
        if barbero_id:
            qs = qs.filter(barbero_id=barbero_id)
        return qs

    def create(self, request, *args, **kwargs):
        # `barbero` participa del unique_together del modelo, así que DRF
        # fuerza required=True en ese campo pase lo que pase en extra_kwargs
        # del serializer — hay que inyectarlo en los datos ANTES de is_valid(),
        # no dejárselo a perform_create() (que corre después de validar).
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        usuario = request.user
        if _es_admin(usuario):
            if not data.get('barbero'):
                raise ValidationError({'barbero': 'Este campo es obligatorio.'})
        else:
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None:
                raise PermissionDenied('Tu usuario no tiene un perfil de Barbero asociado.')
            data['barbero'] = barbero.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        horario = serializer.validated_data.get('horario')
        barbero = serializer.validated_data.get('barbero')
        if horario and barbero and horario.barbero_id != barbero.id:
            raise ValidationError({'horario': 'El horario no pertenece a este barbero.'})

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BarberoServicioDetailView(SoftDeleteMixin, generics.RetrieveUpdateDestroyAPIView):
    """GET público (solo activos, salvo admin/dueño). PATCH/DELETE: dueño
    (barbero) o Admin. DELETE es soft delete (activo=False)."""
    serializer_class = BarberoServicioSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD'):
            return [AllowAny()]
        return [IsAuthenticated(), EsBarberoOAdmin()]

    def get_queryset(self):
        qs = BarberoServicio.objects.select_related('barbero__usuario', 'servicio', 'horario')
        usuario = self.request.user
        if self.request.method in ('GET', 'HEAD') and not _es_admin(usuario):
            qs = qs.filter(activo=True)
        return qs

    def get_object(self):
        obj = super().get_object()
        usuario = self.request.user
        if self.request.method not in ('GET', 'HEAD') and not _es_admin(usuario):
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None or obj.barbero_id != barbero.id:
                raise PermissionDenied('No podés modificar servicios de otro barbero.')
        return obj
