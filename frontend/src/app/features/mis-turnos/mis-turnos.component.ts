import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { TurnoService } from '../../core/services/turno.service';
import { Pagina, TurnoResumen } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

const ESTADO_CLASSES: Record<string, string> = {
  pendiente: 'bg-[rgba(224,197,111,0.15)] text-bl-warning',
  confirmado: 'bg-[rgba(111,170,224,0.15)] text-[#6faae0]',
  completado: 'bg-[rgba(111,224,154,0.15)] text-bl-success',
  cancelado: 'bg-[rgba(224,111,111,0.15)] text-bl-danger',
};

@Component({
  selector: 'app-mis-turnos',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarComponent],
  templateUrl: './mis-turnos.component.html',
})
export class MisTurnosComponent implements OnInit {
  private turnoService = inject(TurnoService);
  private router = inject(Router);
  authService = inject(AuthService);

  pagina = signal<Pagina<TurnoResumen> | null>(null);
  paginaActual = signal(1);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  cancelandoId = signal<number | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(page = 1): void {
    this.loading.set(true);
    this.errorMsg.set(null);
    this.turnoService.misTurnos(page).subscribe({
      next: (res) => {
        this.pagina.set(res);
        this.paginaActual.set(page);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudieron cargar tus turnos.');
      },
    });
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

  estadoClasses(estado: string): string {
    return `inline-block rounded-full px-2 py-0.5 text-[10.5px] capitalize ${ESTADO_CLASSES[estado] ?? ''}`;
  }

  cancelar(turno: TurnoResumen): void {
    this.cancelandoId.set(turno.id);
    this.errorMsg.set(null);
    this.turnoService.cancelar(turno.id).subscribe({
      next: () => {
        this.cancelandoId.set(null);
        this.cargar(this.paginaActual());
      },
      error: (err) => {
        this.cancelandoId.set(null);
        this.errorMsg.set(err?.error?.detail || 'No se pudo cancelar el turno.');
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
