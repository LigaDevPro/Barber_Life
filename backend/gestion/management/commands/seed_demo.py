"""
Comando de seed para tener datos reales (no hardcodeados en el frontend) desde
el primer arranque. Crea: un Administrador, un Barbero, varios Clientes, el
catálogo de Servicios, Horarios, BarberoServicio y Turnos de ejemplo para
hoy y esta semana.

Uso:
    python manage.py seed_demo
"""
import random
from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from gestion.models import Usuario, Cliente, Barbero, Servicio, Horario, BarberoServicio, Turno, Pago


class Command(BaseCommand):
    help = 'Crea datos de demostración para Barber Life (Sprint 2).'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de demo...')

        admin, created = Usuario.objects.get_or_create(
            username='admin@barberlife.com',
            defaults={'email': 'admin@barberlife.com', 'rol': Usuario.Rol.ADMIN,
                      'first_name': 'Miguel', 'last_name': 'Scaccia', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
            self.stdout.write(self.style.SUCCESS('  Admin creado: admin@barberlife.com / admin1234'))

        barbero_user, created = Usuario.objects.get_or_create(
            username='barbero@barberlife.com',
            defaults={'email': 'barbero@barberlife.com', 'rol': Usuario.Rol.BARBERO,
                      'first_name': 'Rodrigo', 'last_name': 'Rojas'},
        )
        if created:
            barbero_user.set_password('barbero1234')
            barbero_user.save()
            self.stdout.write(self.style.SUCCESS('  Barbero creado: barbero@barberlife.com / barbero1234'))

        barbero, _ = Barbero.objects.get_or_create(usuario=barbero_user)

        # Horario laboral de lunes a sábado, 9 a 19hs (necesario porque
        # BARBERO_SERVICIO ahora exige un id_horario).
        horarios = []
        for dia in range(1, 7):  # 1=Lunes ... 6=Sábado
            horario, _ = Horario.objects.get_or_create(
                barbero=barbero, dia_semana=dia,
                defaults={'hora_inicio': time(9, 0), 'hora_fin': time(19, 0), 'intervalo_minutos': 30},
            )
            horarios.append(horario)

        servicios_data = [
            ('Corte de pelo', 15.00, 30),
            ('Coloración', 25.00, 60),
            ('Barba', 10.00, 20),
        ]
        servicios = []
        for nombre, precio, duracion in servicios_data:
            servicio, _ = Servicio.objects.get_or_create(
                nombre=nombre, defaults={'precio': precio, 'duracion_minutos': duracion}
            )
            servicios.append(servicio)
            # Un BarberoServicio por cada franja horaria que tenga el barbero.
            for horario in horarios:
                BarberoServicio.objects.get_or_create(barbero=barbero, servicio=servicio, horario=horario)

        clientes_data = [
            ('Juan', 'Pérez'), ('María', 'López'), ('Carlos', 'Gómez'), ('Carlos', 'Ruiz'),
            ('Lucía', 'Fernández'), ('Martín', 'Díaz'), ('Sofía', 'Torres'),
        ]
        clientes = []
        for i, (nombre, apellido) in enumerate(clientes_data):
            email = f'{nombre.lower()}.{apellido.lower()}{i}@mail.com'
            user, created = Usuario.objects.get_or_create(
                username=email,
                defaults={'email': email, 'rol': Usuario.Rol.CLIENTE, 'first_name': nombre, 'last_name': apellido},
            )
            if created:
                user.set_password('cliente1234')
                user.save()
            cliente, _ = Cliente.objects.get_or_create(usuario=user)
            clientes.append(cliente)

        hoy = timezone.localdate()
        creados = 0
        for offset in range(-3, 4):  # una semana: 3 días atrás a 3 adelante
            fecha = hoy + timedelta(days=offset)
            cantidad_turnos = random.randint(1, 5) if offset <= 0 else random.randint(0, 3)
            horas_usadas = set()
            for _ in range(cantidad_turnos):
                hora = random.choice([h for h in range(9, 19) if h not in horas_usadas])
                horas_usadas.add(hora)
                cliente = random.choice(clientes)
                servicio = random.choice(servicios)
                hora_inicio = time(hora, 0)
                fin_dt = timezone.datetime.combine(fecha, hora_inicio) + timedelta(minutes=servicio.duracion_minutos)
                hora_fin = fin_dt.time()
                estado = Turno.Estado.COMPLETADO if offset < 0 else (
                    Turno.Estado.CONFIRMADO if offset == 0 else Turno.Estado.PENDIENTE)

                turno, created = Turno.objects.get_or_create(
                    barbero=barbero, fecha_turno=fecha, hora_inicio=hora_inicio,
                    defaults={
                        'cliente': cliente, 'servicio': servicio, 'hora_fin': hora_fin,
                        'estado': estado,
                    },
                )
                if created:
                    creados += 1
                    if estado == Turno.Estado.COMPLETADO:
                        Pago.objects.get_or_create(
                            turno=turno,
                            defaults={
                                'monto_total': servicio.precio,
                                'estado': Pago.Estado.APROBADO,
                                'fecha_pago': timezone.now(),
                            },
                        )

        self.stdout.write(self.style.SUCCESS(f'  {creados} turnos de ejemplo creados.'))
        self.stdout.write(self.style.SUCCESS('Listo. Podés loguearte con barbero@barberlife.com / barbero1234'))
