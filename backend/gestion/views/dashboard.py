from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Cliente, Turno, Pago
from ..permissions import EsBarberoOAdmin
from ..serializers import TurnoListSerializer

# ---------------------------------------------------------------------------
# Dashboard — CU-07. RBAC: admin ve ingresos, barbero NO (wiki: "restricción
# financiera para barberos: solo ven volumen de trabajo").
# ---------------------------------------------------------------------------

DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']


class DashboardView(APIView):
    permission_classes = (IsAuthenticated, EsBarberoOAdmin)

    def get(self, request):
        usuario = request.user
        es_admin = usuario.rol == 'admin'

        turnos_qs = Turno.objects.all()
        if not es_admin:
            barbero = getattr(usuario, 'barbero', None)
            if barbero is None:
                return Response(
                    {'detail': 'Tu usuario tiene rol barbero pero no tiene perfil de Barbero asociado. '
                                'Pedile al administrador que lo cree desde /admin/.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            turnos_qs = turnos_qs.filter(barbero=barbero)

        hoy = timezone.localdate()
        turnos_hoy = turnos_qs.filter(fecha_turno=hoy).exclude(estado=Turno.Estado.CANCELADO).count()

        if es_admin:
            clientes_activos = Cliente.objects.filter(activo=True).count()
        else:
            clientes_activos = turnos_qs.values('cliente').distinct().count()

        ingresos_del_mes = None
        if es_admin:
            inicio_mes = hoy.replace(day=1)
            ingresos_del_mes = Pago.objects.filter(
                estado=Pago.Estado.APROBADO,
                fecha_pago__date__gte=inicio_mes,
            ).aggregate(total=Sum('monto_total'))['total'] or 0

        # Turnos por semana: últimos 7 días con datos reales (no placeholder)
        inicio_semana = hoy - timedelta(days=6)
        conteos = (
            turnos_qs.filter(fecha_turno__gte=inicio_semana)
            .exclude(estado=Turno.Estado.CANCELADO)
            .values_list('fecha_turno', flat=True)
        )
        conteo_por_dia = {}
        for fecha in conteos:
            conteo_por_dia[fecha] = conteo_por_dia.get(fecha, 0) + 1
        turnos_por_semana = []
        for i in range(7):
            dia = inicio_semana + timedelta(days=i)
            turnos_por_semana.append({
                'dia': DIAS_CORTOS[dia.weekday()],
                'cantidad': conteo_por_dia.get(dia, 0),
            })

        ultimos_turnos = turnos_qs.exclude(estado=Turno.Estado.CANCELADO).order_by('-fecha_creacion')[:5]
        ultimos_turnos_data = TurnoListSerializer(ultimos_turnos, many=True).data

        return Response({
            'rol': usuario.rol,
            'nombre': usuario.get_full_name() or usuario.email.split('@')[0],
            'turnos_hoy': turnos_hoy,
            'clientes_activos': clientes_activos,
            'ingresos_del_mes': ingresos_del_mes,
            'turnos_por_semana': turnos_por_semana,
            'ultimos_turnos': ultimos_turnos_data,
        })
