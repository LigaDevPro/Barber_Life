import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { NotificacionService } from '../../core/services/notificacion.service';
import { Notificacion, Pagina } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

@Component({
  selector: 'app-notificaciones',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './notificaciones.component.html',
})
export class NotificacionesComponent implements OnInit {
  private notificacionService = inject(NotificacionService);
  private router = inject(Router);
  authService = inject(AuthService);

  pagina = signal<Pagina<Notificacion> | null>(null);
  paginaActual = signal(1);
  soloNoLeidas = signal(false);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  marcandoId = signal<string | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(page = 1): void {
    this.loading.set(true);
    this.errorMsg.set(null);
    this.notificacionService.listar(page, this.soloNoLeidas() ? false : undefined).subscribe({
      next: (res) => {
        this.pagina.set(res);
        this.paginaActual.set(page);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudieron cargar las notificaciones.');
      },
    });
  }

  cambiarFiltro(soloNoLeidas: boolean): void {
    this.soloNoLeidas.set(soloNoLeidas);
    this.cargar(1);
  }

  irAPagina(page: number): void {
    const p = this.pagina();
    if (page < 1 || (p && page > p.num_pages)) return;
    this.cargar(page);
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

  marcarLeida(n: Notificacion): void {
    if (n.leida) return;
    this.marcandoId.set(n.id);
    this.notificacionService.marcarLeida(n.id).subscribe({
      next: () => {
        this.marcandoId.set(null);
        const p = this.pagina();
        if (!p) return;
        if (this.soloNoLeidas()) {
          this.cargar(this.paginaActual());
        } else {
          this.pagina.set({ ...p, results: p.results.map((r) => (r.id === n.id ? { ...r, leida: true } : r)) });
        }
      },
      error: () => {
        this.marcandoId.set(null);
        this.errorMsg.set('No se pudo marcar como leída.');
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
