"""
Modelos relacionales — Sistema Barber Life
Actualizado para coincidir exactamente con el DER definitivo (versión con
BARBERO_SERVICIO ligado a HORARIOS y TURNOS con fecha/hora separadas).
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class Usuario(AbstractUser):
    """USUARIOS — autenticación + rol (base de todo el RBAC)."""

    class Rol(models.TextChoices):
        CLIENTE = 'cliente', 'Cliente'
        BARBERO = 'barbero', 'Barbero'
        ADMIN = 'admin', 'Administrador'

    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        INACTIVO = 'inactivo', 'Inactivo'

    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.CLIENTE)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    telefono = models.CharField(max_length=30, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Mantiene sincronizado el flag interno de Django (is_active, usado por
        # el framework de auth) con el campo `estado` explícito del DER.
        self.is_active = self.estado == self.Estado.ACTIVO
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.rol})'


class Cliente(models.Model):
    """CLIENTES"""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f'Cliente: {self.usuario}'


class Barbero(models.Model):
    """BARBEROS"""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='barbero')
    foto_perfil_url = models.URLField(max_length=500, blank=True, default='')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Barbero: {self.usuario}'


class Servicio(models.Model):
    """SERVICIOS"""
    nombre = models.CharField(max_length=150)
    duracion_minutos = models.PositiveIntegerField(default=30)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Horario(models.Model):
    """HORARIOS — disponibilidad semanal de cada barbero."""
    DIAS_SEMANA = [(i, d) for i, d in enumerate(
        ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'], start=1)]

    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    intervalo_minutos = models.PositiveIntegerField(default=30)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f'{self.barbero} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}'


class BarberoServicio(models.Model):
    """BARBERO_SERVICIO — qué servicios ofrece cada barbero, en qué franja
    horaria (id_horario) y a qué precio (con override opcional)."""
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='servicios_ofrecidos')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='barberos_que_lo_ofrecen')
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='servicios_disponibles')
    precio_personalizado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('barbero', 'servicio', 'horario')

    def precio_final(self):
        return self.precio_personalizado if self.precio_personalizado is not None else self.servicio.precio

    def __str__(self):
        return f'{self.barbero} - {self.servicio} ({self.horario})'


class Turno(models.Model):
    """TURNOS — núcleo del sistema. fecha/hora_inicio/hora_fin separadas,
    igual que en el DER (no un único DateTimeField)."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CONFIRMADO = 'confirmado', 'Confirmado'
        COMPLETADO = 'completado', 'Completado'
        CANCELADO = 'cancelado', 'Cancelado'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='turnos')
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='turnos')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name='turnos')
    fecha_turno = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    observaciones = models.TextField(blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_turno', '-hora_inicio']
        indexes = [models.Index(fields=['barbero', 'fecha_turno'])]

    def clean(self):
        """Prevención de superposición de turnos (wiki: 'no pueden existir dos
        turnos simultáneos para el mismo barbero'), comparando dentro del
        mismo día (fecha_turno) los rangos hora_inicio/hora_fin."""
        if self.barbero_id and self.fecha_turno and self.hora_inicio and self.hora_fin:
            solapados = Turno.objects.filter(
                barbero_id=self.barbero_id,
                fecha_turno=self.fecha_turno,
                hora_inicio__lt=self.hora_fin,
                hora_fin__gt=self.hora_inicio,
            ).exclude(estado=Turno.Estado.CANCELADO).exclude(pk=self.pk)
            if solapados.exists():
                raise ValidationError('El barbero ya tiene un turno reservado en ese horario.')

    def inicio_datetime(self):
        """Combina fecha_turno + hora_inicio en un datetime tz-aware, útil
        para comparar contra `timezone.now()` (ventana de cancelación, etc.)."""
        naive = datetime.combine(self.fecha_turno, self.hora_inicio)
        return timezone.make_aware(naive) if timezone.is_naive(naive) else naive

    def precio(self):
        """El DER ya no guarda precio_total en Turno; se calcula desde el
        precio vigente del Servicio (o el personalizado de BarberoServicio,
        si el barbero tiene uno cargado para ese servicio)."""
        bs = BarberoServicio.objects.filter(
            barbero_id=self.barbero_id, servicio_id=self.servicio_id, activo=True
        ).first()
        return bs.precio_final() if bs else self.servicio.precio

    def puede_cancelar_cliente(self):
        """Política de cancelación autónoma: solo dentro de la ventana definida
        (settings.CANCELACION_LIMITE_HORAS, wiki: 'ej. hasta 2 horas antes')."""
        from django.conf import settings as dj_settings
        limite = getattr(dj_settings, 'CANCELACION_LIMITE_HORAS', 2)
        return timezone.now() <= self.inicio_datetime() - timedelta(hours=limite)

    def __str__(self):
        return f'Turno #{self.pk} - {self.cliente} con {self.barbero} - {self.fecha_turno} {self.hora_inicio}'


class Pago(models.Model):
    """PAGOS"""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'
        REEMBOLSADO = 'reembolsado', 'Reembolsado'

    class Metodo(models.TextChoices):
        MERCADO_PAGO = 'mercado_pago', 'Mercado Pago'
        EFECTIVO = 'efectivo', 'Efectivo'

    turno = models.OneToOneField(Turno, on_delete=models.CASCADE, related_name='pago')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=Metodo.choices, default=Metodo.MERCADO_PAGO)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    comprobante_url = models.URLField(max_length=500, blank=True, null=True)
    transaccion_id = models.CharField(max_length=255, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago #{self.pk} - {self.estado} - ${self.monto_total}'


class EstadisticaDiaria(models.Model):
    """ESTADISTICAS_DIARIAS — reporte diario por barbero (obligatorio, no
    admite null: cada fila es la estadística de UN barbero en UNA fecha)."""
    fecha = models.DateField()
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='estadisticas')
    turnos_realizados = models.PositiveIntegerField(default=0)
    ingresos_totales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    clientes_unicos = models.PositiveIntegerField(default=0)
    # Sin FK real en el DER (es un int suelto, no una llave) — se resuelve
    # contra Servicio.id manualmente desde el código si hace falta mostrarlo.
    servicio_mas_solicitado = models.PositiveIntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fecha', 'barbero')
        ordering = ['-fecha']

    def __str__(self):
        return f'Estadística {self.fecha} - {self.barbero}'
