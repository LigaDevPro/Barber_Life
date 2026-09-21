import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { BarberoService } from '../../core/services/barbero.service';
import { CatalogoService } from '../../core/services/catalogo.service';
import { BarberoPublic, BarberoServicio, Horario, Servicio } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

export const DIAS_SEMANA = [
  { valor: 1, nombre: 'Lunes' },
  { valor: 2, nombre: 'Martes' },
  { valor: 3, nombre: 'Miércoles' },
  { valor: 4, nombre: 'Jueves' },
  { valor: 5, nombre: 'Viernes' },
  { valor: 6, nombre: 'Sábado' },
  { valor: 7, nombre: 'Domingo' },
];

type Tab = 'servicios' | 'horarios' | 'oferta';

/** Extrae el primer mensaje de error legible de una respuesta 400 de DRF,
 * que puede venir como {detail: "..."} o como {campo: ["..."]}. */
function primerError(err: unknown): string | null {
  const data = (err as { error?: Record<string, unknown> })?.error;
  if (!data) return null;
  if (typeof data['detail'] === 'string') return data['detail'];
  const primerValor = Object.values(data)[0];
  return Array.isArray(primerValor) ? String(primerValor[0]) : typeof primerValor === 'string' ? primerValor : null;
}

@Component({
  selector: 'app-catalogo',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TopbarComponent],
  templateUrl: './catalogo.component.html',
})
export class CatalogoComponent implements OnInit {
  private fb = inject(FormBuilder);
  private catalogoService = inject(CatalogoService);
  private barberoService = inject(BarberoService);
  private router = inject(Router);
  authService = inject(AuthService);

  dias = DIAS_SEMANA;
  tab = signal<Tab>('servicios');
  esAdmin = computed(() => this.authService.currentUser()?.rol === 'admin');

  loading = signal(true);
  errorMsg = signal<string | null>(null);

  servicios = signal<Servicio[]>([]);
  barberos = signal<BarberoPublic[]>([]);
  barberoIdPropio = signal<number | null>(null);
  barberoSeleccionadoId = signal<number | null>(null);
  barberoActivoId = computed(() => (this.esAdmin() ? this.barberoSeleccionadoId() : this.barberoIdPropio()));

  horarios = signal<Horario[]>([]);
  ofertas = signal<BarberoServicio[]>([]);
  serviciosActivos = computed(() => this.servicios().filter((s) => s.activo));
  horariosActivos = computed(() => this.horarios().filter((h) => h.activo));

  formServicio = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    duracion_minutos: [30, [Validators.required, Validators.min(1)]],
    precio: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,2})?$/)]],
  });
  editandoServicioId = signal<number | null>(null);
  guardandoServicio = signal(false);

  formHorario = this.fb.nonNullable.group({
    dia_semana: [1, Validators.required],
    hora_inicio: ['09:00', Validators.required],
    hora_fin: ['18:00', Validators.required],
    intervalo_minutos: [30, [Validators.required, Validators.min(5)]],
  });
  guardandoHorario = signal(false);

  formOferta = this.fb.group({
    servicio: this.fb.control<number | null>(null, Validators.required),
    horario: this.fb.control<number | null>(null, Validators.required),
    precio_personalizado: this.fb.nonNullable.control(''),
  });
  guardandoOferta = signal(false);

  ngOnInit(): void {
    this.catalogoService.listarServicios().subscribe({ next: (res) => this.servicios.set(res) });

    if (this.esAdmin()) {
      this.barberoService.listar().subscribe({
        next: (res) => {
          this.barberos.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
    } else {
      this.barberoService.getMe().subscribe({
        next: (me) => {
          this.barberoIdPropio.set(me.id);
          this.cargarHorariosYOferta();
          this.loading.set(false);
        },
        error: () => {
          this.errorMsg.set('Tu usuario no tiene un perfil de Barbero asociado.');
          this.loading.set(false);
        },
      });
    }
  }

  cambiarTab(t: Tab): void {
    this.tab.set(t);
  }

  elegirBarbero(idTexto: string): void {
    const id = Number(idTexto) || null;
    this.barberoSeleccionadoId.set(id);
    this.horarios.set([]);
    this.ofertas.set([]);
    if (id) this.cargarHorariosYOferta();
  }

  private cargarHorariosYOferta(): void {
    const barberoId = this.barberoActivoId();
    this.catalogoService.listarHorarios(this.esAdmin() ? (barberoId ?? undefined) : undefined).subscribe({
      next: (res) => this.horarios.set(res),
      error: () => this.horarios.set([]),
    });
    this.catalogoService.listarBarberoServicio(barberoId ?? undefined).subscribe({
      next: (res) => this.ofertas.set(res),
      error: () => this.ofertas.set([]),
    });
  }

  diaNombre(v: number): string {
    return this.dias.find((d) => d.valor === v)?.nombre ?? '';
  }

  // --- Servicio ---
  editarServicio(s: Servicio): void {
    this.editandoServicioId.set(s.id);
    this.formServicio.setValue({ nombre: s.nombre, duracion_minutos: s.duracion_minutos, precio: s.precio });
  }

  cancelarEdicionServicio(): void {
    this.editandoServicioId.set(null);
    this.formServicio.reset({ nombre: '', duracion_minutos: 30, precio: '' });
  }

  guardarServicio(): void {
    if (this.formServicio.invalid) {
      this.formServicio.markAllAsTouched();
      return;
    }
    this.guardandoServicio.set(true);
    this.errorMsg.set(null);
    const payload = this.formServicio.getRawValue();
    const id = this.editandoServicioId();
    const obs = id
      ? this.catalogoService.actualizarServicio(id, payload)
      : this.catalogoService.crearServicio(payload);
    obs.subscribe({
      next: () => {
        this.guardandoServicio.set(false);
        this.cancelarEdicionServicio();
        this.catalogoService.listarServicios().subscribe((res) => this.servicios.set(res));
      },
      error: (err) => {
        this.guardandoServicio.set(false);
        this.errorMsg.set(primerError(err) || 'No se pudo guardar el servicio.');
      },
    });
  }

  toggleServicio(s: Servicio): void {
    this.errorMsg.set(null);
    const refrescar = () => this.catalogoService.listarServicios().subscribe((res) => this.servicios.set(res));
    const error = () => this.errorMsg.set('No se pudo actualizar el servicio.');
    if (s.activo) {
      this.catalogoService.desactivarServicio(s.id).subscribe({ next: refrescar, error });
    } else {
      this.catalogoService.actualizarServicio(s.id, { activo: true }).subscribe({ next: refrescar, error });
    }
  }

  // --- Horario ---
  guardarHorario(): void {
    if (this.formHorario.invalid) {
      this.formHorario.markAllAsTouched();
      return;
    }
    const barberoId = this.barberoActivoId();
    if (this.esAdmin() && !barberoId) {
      this.errorMsg.set('Elegí un barbero primero.');
      return;
    }
    this.guardandoHorario.set(true);
    this.errorMsg.set(null);
    const raw = this.formHorario.getRawValue();
    this.catalogoService
      .crearHorario({
        barbero: barberoId!,
        dia_semana: raw.dia_semana!,
        hora_inicio: raw.hora_inicio!,
        hora_fin: raw.hora_fin!,
        intervalo_minutos: raw.intervalo_minutos!,
      })
      .subscribe({
        next: () => {
          this.guardandoHorario.set(false);
          this.formHorario.reset({ dia_semana: 1, hora_inicio: '09:00', hora_fin: '18:00', intervalo_minutos: 30 });
          this.cargarHorariosYOferta();
        },
        error: (err) => {
          this.guardandoHorario.set(false);
          this.errorMsg.set(primerError(err) || 'No se pudo crear el horario.');
        },
      });
  }

  toggleHorario(h: Horario): void {
    this.errorMsg.set(null);
    const next = () => this.cargarHorariosYOferta();
    const error = () => this.errorMsg.set('No se pudo actualizar el horario.');
    if (h.activo) {
      this.catalogoService.desactivarHorario(h.id).subscribe({ next, error });
    } else {
      this.catalogoService.actualizarHorario(h.id, { activo: true }).subscribe({ next, error });
    }
  }

  // --- Oferta (BarberoServicio) ---
  guardarOferta(): void {
    if (this.formOferta.invalid) {
      this.formOferta.markAllAsTouched();
      return;
    }
    const barberoId = this.barberoActivoId();
    if (this.esAdmin() && !barberoId) {
      this.errorMsg.set('Elegí un barbero primero.');
      return;
    }
    this.guardandoOferta.set(true);
    this.errorMsg.set(null);
    const raw = this.formOferta.getRawValue();
    this.catalogoService
      .crearBarberoServicio({
        barbero: barberoId!,
        servicio: raw.servicio!,
        horario: raw.horario!,
        precio_personalizado: raw.precio_personalizado ? raw.precio_personalizado : null,
      })
      .subscribe({
        next: () => {
          this.guardandoOferta.set(false);
          this.formOferta.reset({ servicio: null, horario: null, precio_personalizado: '' });
          this.cargarHorariosYOferta();
        },
        error: (err) => {
          this.guardandoOferta.set(false);
          this.errorMsg.set(primerError(err) || 'No se pudo crear la oferta.');
        },
      });
  }

  toggleOferta(o: BarberoServicio): void {
    this.errorMsg.set(null);
    const next = () => this.cargarHorariosYOferta();
    const error = () => this.errorMsg.set('No se pudo actualizar la oferta.');
    if (o.activo) {
      this.catalogoService.desactivarBarberoServicio(o.id).subscribe({ next, error });
    } else {
      this.catalogoService.actualizarBarberoServicio(o.id, { activo: true }).subscribe({ next, error });
    }
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
