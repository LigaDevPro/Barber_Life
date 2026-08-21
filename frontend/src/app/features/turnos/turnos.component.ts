import { Component, OnInit, signal } from '@angular/core';
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

@Component({
  selector: 'app-turnos',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './turnos.component.html',
  styleUrl: './turnos.component.scss',
})
export class TurnosComponent implements OnInit {
  servicios = signal<ServicioMasSolicitado[]>([]);
  pagina = signal<TurnosPage | null>(null);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  menuAbierto = signal<number | null>(null);
  paginaActual = signal(1);

  constructor(private panelService: PanelService, public authService: AuthService, private router: Router) {}

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
