from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Cliente, Barbero, Servicio, BarberoServicio,
    Horario, Turno, Pago, EstadisticaDiaria,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'estado')
    list_filter = ('rol', 'estado')
    fieldsets = UserAdmin.fieldsets + (
        ('Barber Life', {'fields': ('rol', 'estado', 'telefono')}),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_registro', 'activo')


@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'foto_perfil_url', 'activo')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion_minutos', 'activo')


@admin.register(BarberoServicio)
class BarberoServicioAdmin(admin.ModelAdmin):
    list_display = ('barbero', 'servicio', 'horario', 'precio_personalizado', 'activo')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('barbero', 'dia_semana', 'hora_inicio', 'hora_fin', 'activo')


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'barbero', 'servicio', 'fecha_turno', 'hora_inicio', 'estado')
    list_filter = ('estado', 'barbero')


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'turno', 'monto_total', 'metodo_pago', 'estado')


@admin.register(EstadisticaDiaria)
class EstadisticaDiariaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'barbero', 'turnos_realizados', 'ingresos_totales')
