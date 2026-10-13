import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { PanelService } from '../../core/auth/panel.service';
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
  confirmado: 'bg-bl-info/15 text-bl-info',
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

  /** Filtros (Mejora 4 de Figma: «Hoy», «Mañana», «Esta semana» y selector de fecha): rango rápido, fecha puntual, estado y búsqueda. */
  readonly rangos = [
    { valor: 'todos', etiqueta: 'Todos' },
    { valor: 'hoy', etiqueta: 'Hoy' },
    { valor: 'manana', etiqueta: 'Mañana' },
    { valor: 'semana', etiqueta: 'Esta semana' },
  ] as const;
  rango = signal<'todos' | 'hoy' | 'manana' | 'semana'>('hoy');
  fechaSeleccionada = signal('');
  selectorFechaAbierto = signal(false);

  /** Resultados de la página actual con el filtro de fecha aplicado. */
  resultadosFiltrados = computed<TurnoResumen[]>(() => {
    const p = this.pagina();
    if (!p) return [];
    const fecha = this.fechaSeleccionada();
    const rango = this.rango();
    return p.results.filter((t) => {
      if (fecha) return t.fecha === fecha;
      if (rango === 'todos') return true;
      const hoy = this.iso(new Date());
      if (rango === 'hoy') return t.fecha === hoy;
      if (rango === 'manana') return t.fecha === this.iso(this.sumarDias(new Date(), 1));
      const lunes = this.sumarDias(new Date(), -((new Date().getDay() + 6) % 7));
      return t.fecha >= this.iso(lunes) && t.fecha <= this.iso(this.sumarDias(lunes, 6));
    });
  });

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
    this.panelService.getTurnos(page).subscribe({
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
    this.rango.set(this.rango() === valor && !this.fechaSeleccionada() ? 'todos' : valor);
    this.fechaSeleccionada.set('');
    this.selectorFechaAbierto.set(false);
  }

  toggleSelectorFecha(): void {
    this.selectorFechaAbierto.update((v) => !v);
  }

  elegirFecha(valor: string): void {
    this.fechaSeleccionada.set(valor);
    if (valor) this.rango.set('todos');
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
