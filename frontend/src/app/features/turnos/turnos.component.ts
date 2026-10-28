import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FiltrosTurnos, PanelService } from '../../core/auth/panel.service';
import { AuthService } from '../../core/auth/auth.service';
import { ServicioMasSolicitado, TurnoResumen, TurnosPage } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

const ICONOS_SERVICIO: Record<string, string> = {
  corte: 'scissors',
  barba: 'razor',
  color: 'drop',
};

const ESTADO_CLASSES: Record<string, string> = {
  pendiente: 'bg-bl-warning/15 text-bl-warning',
  confirmado: 'bg-bl-info/15 text-bl-info-text',
  completado: 'bg-bl-success/15 text-bl-success',
  cancelado: 'bg-bl-danger/15 text-bl-danger-text',
};

@Component({
  selector: 'app-turnos',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './turnos.component.html',
})
export class TurnosComponent implements OnInit {
  servicios = signal<ServicioMasSolicitado[]>([]);
  pagina = signal<TurnosPage | null>(null);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  menuAbierto = signal<number | null>(null);
  paginaActual = signal(1);

  /** Filtros combinables (todos se aplican en el servidor): rango rápido («Hoy», «Mañana», «Esta semana»), rango de fechas propio, estado y texto. */
  readonly rangos = [
    { valor: 'todos', etiqueta: 'Todos' },
    { valor: 'hoy', etiqueta: 'Hoy' },
    { valor: 'manana', etiqueta: 'Mañana' },
    { valor: 'semana', etiqueta: 'Esta semana' },
  ] as const;
  readonly estados = [
    { valor: '', etiqueta: 'Todos los estados' },
    { valor: 'pendiente', etiqueta: 'Pendiente' },
    { valor: 'confirmado', etiqueta: 'Confirmado' },
    { valor: 'completado', etiqueta: 'Completado' },
    { valor: 'cancelado', etiqueta: 'Cancelado' },
  ] as const;
  rango = signal<'todos' | 'hoy' | 'manana' | 'semana'>('hoy');
  fechaDesde = signal('');
  fechaHasta = signal('');
  estado = signal('');
  busqueda = signal('');
  selectorFechaAbierto = signal(false);
  exportando = signal(false);

  /** Hay un rango de fechas propio cargado (tiene prioridad sobre los chips). */
  rangoPropio = computed(() => !!(this.fechaDesde() || this.fechaHasta()));

  /** Resultados de la página actual (el filtrado ya viene hecho por el backend). */
  resultados = computed<TurnoResumen[]>(() => this.pagina()?.results ?? []);

  /** Traduce el estado de los controles a los parámetros que entiende la API. */
  private filtros(): FiltrosTurnos {
    const filtros: FiltrosTurnos = { q: this.busqueda().trim(), estado: this.estado() };
    if (this.rangoPropio()) {
      filtros.fechaDesde = this.fechaDesde();
      filtros.fechaHasta = this.fechaHasta();
    } else if (this.rango() === 'hoy') {
      filtros.fechaDesde = filtros.fechaHasta = this.iso(new Date());
    } else if (this.rango() === 'manana') {
      filtros.fechaDesde = filtros.fechaHasta = this.iso(this.sumarDias(new Date(), 1));
    } else if (this.rango() === 'semana') {
      const lunes = this.sumarDias(new Date(), -((new Date().getDay() + 6) % 7));
      filtros.fechaDesde = this.iso(lunes);
      filtros.fechaHasta = this.iso(this.sumarDias(lunes, 6));
    }
    return filtros;
  }

  constructor(
    private panelService: PanelService,
    public authService: AuthService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.cargarServicios();
    this.cargarTurnos();
  }

  cargarServicios(): void {
    this.panelService.getServiciosMasSolicitados().subscribe({
      next: (res) => this.servicios.set(res),
      error: () => this.servicios.set([]),
    });
  }

  cargarTurnos(page = 1): void {
    this.loading.set(true);
    this.errorMsg.set(null);
    this.panelService.getTurnos(page, this.filtros()).subscribe({
      next: (res) => {
        this.pagina.set(res);
        this.paginaActual.set(page);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudieron cargar los turnos.');
      },
    });
  }

  /** Tocar el chip activo lo apaga y vuelve a mostrar todos los turnos. */
  elegirRango(valor: 'todos' | 'hoy' | 'manana' | 'semana'): void {
    this.rango.set(this.rango() === valor && !this.rangoPropio() ? 'todos' : valor);
    this.fechaDesde.set('');
    this.fechaHasta.set('');
    this.selectorFechaAbierto.set(false);
    this.cargarTurnos();
  }

  toggleSelectorFecha(): void {
    this.selectorFechaAbierto.update((v) => !v);
  }

  elegirFechaDesde(valor: string): void {
    this.fechaDesde.set(valor);
    this.cargarTurnos();
  }

  elegirFechaHasta(valor: string): void {
    this.fechaHasta.set(valor);
    this.cargarTurnos();
  }

  limpiarFechas(): void {
    this.fechaDesde.set('');
    this.fechaHasta.set('');
    this.cargarTurnos();
  }

  elegirEstado(valor: string): void {
    this.estado.set(valor);
    this.cargarTurnos();
  }

  buscar(valor: string): void {
    this.busqueda.set(valor);
    this.cargarTurnos();
  }

  /** Descarga en CSV los turnos que matchean los filtros activos (no solo la página visible). */
  exportarCsv(): void {
    this.exportando.set(true);
    this.errorMsg.set(null);
    this.panelService.exportarTurnos(this.filtros()).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = 'turnos.csv';
        enlace.click();
        URL.revokeObjectURL(url);
        this.exportando.set(false);
      },
      error: () => {
        this.exportando.set(false);
        this.errorMsg.set('No se pudo exportar los turnos.');
      },
    });
  }

  private iso(d: Date): string {
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${m}-${dd}`;
  }

  private sumarDias(d: Date, n: number): Date {
    const r = new Date(d);
    r.setDate(r.getDate() + n);
    return r;
  }

  irAPagina(page: number): void {
    if (page < 1 || (this.pagina() && page > this.pagina()!.num_pages)) return;
    this.cargarTurnos(page);
  }

  toggleMenu(id: number): void {
    this.menuAbierto.set(this.menuAbierto() === id ? null : id);
  }

  cambiarEstado(turno: TurnoResumen, estado: string): void {
    this.menuAbierto.set(null);
    this.panelService.actualizarEstadoTurno(turno.id, estado).subscribe({
      next: () => {
        this.cargarTurnos(this.paginaActual());
      },
      error: () => {
        this.errorMsg.set('No se pudo actualizar el turno.');
      },
    });
  }

  paginasVisibles(): number[] {
    const p = this.pagina();
    if (!p) return [];
    const total = p.num_pages;
    const actual = p.page;
    const inicio = Math.max(1, Math.min(actual - 1, total - 2));
    const fin = Math.min(total, inicio + 2);
    const arr: number[] = [];
    for (let i = inicio; i <= fin; i++) arr.push(i);
    return arr;
  }

  estadoClasses(estado: string): string {
    return `mt-1 inline-block rounded-badge px-2.5 py-0.75 text-[10.5px] capitalize ${ESTADO_CLASSES[estado] ?? ''}`;
  }

  rangoTexto(): string {
    const p = this.pagina();
    if (!p) return '';
    const desde = (p.page - 1) * 7 + 1;
    const hasta = Math.min(p.page * 7, p.count);
    return `Mostrando ${desde} a ${hasta} de ${p.count} resultados`;
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
