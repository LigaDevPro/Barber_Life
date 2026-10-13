import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../../core/auth/auth.service';
import { BarberoService } from '../../core/services/barbero.service';
import { CatalogoService } from '../../core/services/catalogo.service';
import { PagoService } from '../../core/services/pago.service';
import { TurnoService } from '../../core/services/turno.service';
import { BarberoDetail, MetodoPago, Servicio, TurnoResumen } from '../../core/models/models';
import { iconoServicio } from '../../shared/servicio-icono';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

interface DiaOpcion {
  iso: string;
  diaSemana: number;
  dow: string;
  num: string;
  full: string;
}

const DOW_CORTO = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const PASOS_A_SEGUIR = 14;

@Component({
  selector: 'app-solicitar-turno',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarComponent],
  templateUrl: './solicitar-turno.component.html',
})
export class SolicitarTurnoComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private catalogoService = inject(CatalogoService);
  private barberoService = inject(BarberoService);
  private turnoService = inject(TurnoService);
  private pagoService = inject(PagoService);
  authService = inject(AuthService);

  cargando = signal(true);
  errorCarga = signal<string | null>(null);
  errorMsg = signal<string | null>(null);
  enviando = signal(false);
  turnoCreado = signal<TurnoResumen | null>(null);
  avisoPago = signal<string | null>(null);

  servicios = signal<Servicio[]>([]);
  barberos = signal<BarberoDetail[]>([]);

  servicioId = signal<number | null>(null);
  barberoId = signal<number | null>(null);
  diaIso = signal<string | null>(null);
  hora = signal<string | null>(null);
  formaPago = signal<MetodoPago>('efectivo');

  servicioSeleccionado = computed(() => this.servicios().find((s) => s.id === this.servicioId()) ?? null);
  barberoSeleccionado = computed(() => this.barberos().find((b) => b.id === this.barberoId()) ?? null);

  barberosDisponibles = computed(() => {
    const servicioId = this.servicioId();
    if (!servicioId) return this.barberos();
    return this.barberos().filter((b) => b.servicios_ofrecidos.some((so) => so.servicio === servicioId));
  });

  diasDisponibles = computed<DiaOpcion[]>(() => {
    const barbero = this.barberoSeleccionado();
    if (!barbero) return [];
    const diasConHorario = new Set(barbero.horarios.map((h) => h.dia_semana));

    const opciones: DiaOpcion[] = [];
    const hoy = new Date();
    for (let i = 0; i < PASOS_A_SEGUIR && opciones.length < 6; i++) {
      const fecha = new Date(hoy);
      fecha.setDate(hoy.getDate() + i);
      const isoWeekday = fecha.getDay() === 0 ? 7 : fecha.getDay();
      if (!diasConHorario.has(isoWeekday)) continue;

      const iso = fecha.toISOString().slice(0, 10);
      opciones.push({
        iso,
        diaSemana: isoWeekday,
        dow: DOW_CORTO[fecha.getDay()],
        num: String(fecha.getDate()).padStart(2, '0'),
        full: `${DOW_CORTO[fecha.getDay()]} ${String(fecha.getDate()).padStart(2, '0')}/${String(fecha.getMonth() + 1).padStart(2, '0')}`,
      });
    }
    return opciones;
  });

  /** Genera los horarios candidatos combinando el horario laboral del
   * barbero ese día con la duración del servicio — mismo criterio que ya
   * valida `TurnoCreateSerializer.validate()` en el backend (barbero +
   * servicio + horario activo + rango horario), así un slot que se ve acá
   * disponible casi siempre pasa la validación del servidor. */
  horariosDisponibles = computed<string[]>(() => {
    const barbero = this.barberoSeleccionado();
    const servicio = this.servicioSeleccionado();
    const diaIso = this.diaIso();
    const dia = this.diasDisponibles().find((d) => d.iso === diaIso);
    if (!barbero || !servicio || !dia) return [];

    const idsHorarioQueOfrecenServicio = new Set(
      barbero.servicios_ofrecidos.filter((so) => so.servicio === servicio.id).map((so) => so.horario),
    );

    const slots: string[] = [];
    for (const horario of barbero.horarios) {
      if (horario.dia_semana !== dia.diaSemana) continue;
      if (!idsHorarioQueOfrecenServicio.has(horario.id)) continue;

      const [hInicioH, hInicioM] = horario.hora_inicio.split(':').map(Number);
      const [hFinH, hFinM] = horario.hora_fin.split(':').map(Number);
      let minutos = hInicioH * 60 + hInicioM;
      const finMinutos = hFinH * 60 + hFinM;

      while (minutos + servicio.duracion_minutos <= finMinutos) {
        const hh = String(Math.floor(minutos / 60)).padStart(2, '0');
        const mm = String(minutos % 60).padStart(2, '0');
        const slot = `${hh}:${mm}`;
        if (!slots.includes(slot)) slots.push(slot);
        minutos += horario.intervalo_minutos;
      }
    }
    return slots.sort();
  });

  listoParaConfirmar = computed(
    () => !!(this.servicioId() && this.barberoId() && this.diaIso() && this.hora()) && !this.enviando(),
  );

  ngOnInit(): void {
    forkJoin({
      servicios: this.catalogoService.listarServicios().pipe(catchError(() => of([] as Servicio[]))),
      barberosPublicos: this.barberoService.listar().pipe(catchError(() => of([]))),
    }).subscribe(({ servicios, barberosPublicos }) => {
      this.servicios.set(servicios);

      if (barberosPublicos.length === 0) {
        this.barberos.set([]);
        this.aplicarQueryParams();
        this.cargando.set(false);
        return;
      }

      forkJoin(barberosPublicos.map((b) => this.barberoService.detalle(b.id))).subscribe({
        next: (detalles) => {
          this.barberos.set(detalles);
          this.aplicarQueryParams();
          this.cargando.set(false);
        },
        error: () => {
          this.errorCarga.set('No se pudieron cargar los datos para armar el turno.');
          this.cargando.set(false);
        },
      });
    });
  }

  private aplicarQueryParams(): void {
    const servicio = Number(this.route.snapshot.queryParamMap.get('servicio'));
    const barbero = Number(this.route.snapshot.queryParamMap.get('barbero'));
    if (servicio && this.servicios().some((s) => s.id === servicio)) this.servicioId.set(servicio);
    if (barbero && this.barberos().some((b) => b.id === barbero)) this.barberoId.set(barbero);
  }

  icono(nombre: string): string {
    return iconoServicio(nombre);
  }

  elegirServicio(id: number): void {
    this.servicioId.set(id);
    if (this.barberoId() && !this.barberosDisponibles().some((b) => b.id === this.barberoId())) {
      this.barberoId.set(null);
    }
    this.diaIso.set(null);
    this.hora.set(null);
  }

  elegirBarbero(id: number): void {
    this.barberoId.set(id);
    this.diaIso.set(null);
    this.hora.set(null);
  }

  elegirDia(iso: string): void {
    this.diaIso.set(iso);
    this.hora.set(null);
  }

  elegirHora(h: string): void {
    this.hora.set(h);
  }

  elegirPago(m: MetodoPago): void {
    this.formaPago.set(m);
  }

  confirmar(): void {
    const barberoId = this.barberoId();
    const servicioId = this.servicioId();
    const fecha = this.diaIso();
    const hora = this.hora();
    if (!barberoId || !servicioId || !fecha || !hora) return;

    this.enviando.set(true);
    this.errorMsg.set(null);

    this.turnoService
      .crear({ barbero: barberoId, servicio: servicioId, fecha_turno: fecha, hora_inicio: `${hora}:00` })
      .subscribe({
        next: (turno) => {
          this.turnoCreado.set(turno);
          this.enviando.set(false);
          if (this.formaPago() === 'mercado_pago') {
            this.iniciarPago(turno.id);
          }
        },
        error: (err) => {
          this.enviando.set(false);
          const data = err?.error || {};
          const mensaje =
            data.detail || data.barbero?.[0] || data.servicio?.[0] || data.hora_inicio?.[0] || data.fecha_turno?.[0];
          this.errorMsg.set(mensaje || 'No se pudo reservar el turno. Probá con otro horario.');
        },
      });
  }

  private iniciarPago(turnoId: number): void {
    this.pagoService.crear(turnoId).subscribe({
      next: (res) => {
        window.location.href = res.init_point;
      },
      error: () => {
        this.avisoPago.set(
          'El turno quedó reservado, pero no pudimos generar el link de Mercado Pago. Podés pagar en el local.',
        );
      },
    });
  }

  solicitarOtro(): void {
    this.turnoCreado.set(null);
    this.avisoPago.set(null);
    this.errorMsg.set(null);
    this.servicioId.set(null);
    this.barberoId.set(null);
    this.diaIso.set(null);
    this.hora.set(null);
    this.formaPago.set('efectivo');
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
