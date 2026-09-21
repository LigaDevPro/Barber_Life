import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../../core/auth/auth.service';
import { BarberoService } from '../../core/services/barbero.service';
import { CatalogoService } from '../../core/services/catalogo.service';
import { BarberoDetail, ServicioOfrecidoInline, Servicio } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';
import { iconoServicio } from '../../shared/servicio-icono';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, TopbarComponent],
  templateUrl: './inicio.component.html',
})
export class InicioComponent implements OnInit {
  private barberoService = inject(BarberoService);
  private catalogoService = inject(CatalogoService);
  private router = inject(Router);
  authService = inject(AuthService);

  servicios = signal<Servicio[]>([]);
  barberos = signal<BarberoDetail[]>([]);
  loading = signal(true);
  errorMsg = signal<string | null>(null);
  barberoModal = signal<BarberoDetail | null>(null);

  ngOnInit(): void {
    forkJoin({
      servicios: this.catalogoService.listarServicios().pipe(catchError(() => of([] as Servicio[]))),
      barberosPublicos: this.barberoService.listar().pipe(catchError(() => of([]))),
    }).subscribe(({ servicios, barberosPublicos }) => {
      this.servicios.set(servicios);

      if (barberosPublicos.length === 0) {
        this.barberos.set([]);
        this.loading.set(false);
        return;
      }

      forkJoin(barberosPublicos.map((b) => this.barberoService.detalle(b.id))).subscribe({
        next: (detalles) => {
          this.barberos.set(detalles);
          this.loading.set(false);
        },
        error: () => {
          this.errorMsg.set('No se pudo cargar el equipo de barberos.');
          this.loading.set(false);
        },
      });
    });
  }

  icono(nombre: string): string {
    return iconoServicio(nombre);
  }

  /** Un barbero ofrece el mismo servicio una vez por cada horario en que lo
   * ofrece (ver `servicios_ofrecidos` en `BarberoDetail`) — acá se muestra
   * una sola vez por servicio distinto. */
  serviciosDistintos(barbero: BarberoDetail): ServicioOfrecidoInline[] {
    const vistos = new Set<number>();
    return barbero.servicios_ofrecidos.filter((s) => {
      if (vistos.has(s.servicio)) return false;
      vistos.add(s.servicio);
      return true;
    });
  }

  abrirBarbero(barbero: BarberoDetail): void {
    this.barberoModal.set(barbero);
  }

  cerrarModal(): void {
    this.barberoModal.set(null);
  }

  solicitarTurno(opts: { servicioId?: number; barberoId?: number } = {}): void {
    this.barberoModal.set(null);
    this.router.navigate(['/solicitar-turno'], {
      queryParams: { servicio: opts.servicioId ?? null, barbero: opts.barberoId ?? null },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
