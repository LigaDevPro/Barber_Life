import { Component, EventEmitter, Output, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LogoComponent } from '../logo/logo.component';
import { AuthService } from '../../core/auth/auth.service';
import { Rol } from '../../core/models/models';

interface NavItem {
  label: string;
  path: string;
}

/** Navegación por rol. Barbero/Admin comparten hoy el mismo panel; Cliente
 * arranca vacío (sin pantallas propias todavía) — cada paquete que sume una
 * pantalla de Cliente agrega su entrada acá, no hace falta tocar el resto
 * del componente. */
const NAV_POR_ROL: Record<Rol, NavItem[]> = {
  barbero: [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Gestión de turnos', path: '/turnos' },
    { label: 'Mi perfil', path: '/perfil' },
  ],
  admin: [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Gestión de turnos', path: '/turnos' },
  ],
  cliente: [
    { label: 'Inicio', path: '/inicio' },
    { label: 'Mis turnos', path: '/mis-turnos' },
    { label: 'Solicitar turno', path: '/solicitar-turno' },
    { label: 'Mi perfil', path: '/perfil' },
  ],
};

@Component({
  selector: 'bl-topbar',
  standalone: true,
  imports: [CommonModule, RouterLink, LogoComponent],
  template: `
    <header
      class="sticky top-0 z-30 flex items-center justify-between border-b border-bl-border bg-bl-bg px-5 py-4"
    >
      @if (logoPath(); as path) {
        <a [routerLink]="path" class="flex items-center gap-2 text-[15px] font-bold text-bl-text no-underline">
          <bl-logo [size]="28" />
          <span>Barber Life</span>
        </a>
      } @else {
        <span class="flex items-center gap-2 text-[15px] font-bold text-bl-text">
          <bl-logo [size]="28" />
          <span>Barber Life</span>
        </span>
      }

      <button
        class="flex cursor-pointer rounded-field border border-bl-border bg-transparent p-2 text-bl-text transition-colors duration-150 ease-linear hover:bg-bl-surface-2"
        type="button"
        (click)="toggle()"
        aria-label="Menú"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M2 5h16M2 10h16M2 15h16"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
          />
        </svg>
      </button>

      @if (open()) {
        <nav
          class="absolute top-14 right-5 z-20 flex min-w-45 flex-col overflow-hidden rounded-field border border-bl-border bg-bl-surface shadow-[0_12px_30px_rgba(0,0,0,0.45)]"
        >
          @for (item of navItems(); track item.path) {
            <a
              [routerLink]="item.path"
              (click)="open.set(false)"
              class="border-b border-bl-border px-4 py-3 text-left text-[13.5px] text-bl-text no-underline transition-colors duration-150 ease-linear hover:bg-bl-surface-2"
            >
              {{ item.label }}
            </a>
          }
          <button
            type="button"
            (click)="logout.emit()"
            class="cursor-pointer border-0 bg-transparent px-4 py-3 text-left text-[13.5px] text-bl-danger transition-colors duration-150 ease-linear hover:bg-bl-surface-2"
          >
            Cerrar sesión
          </button>
        </nav>
      }
    </header>
  `,
})
export class TopbarComponent {
  @Output() logout = new EventEmitter<void>();
  open = signal(false);

  private authService = inject(AuthService);

  navItems = computed<NavItem[]>(() => {
    const usuario = this.authService.currentUser();
    return usuario ? NAV_POR_ROL[usuario.rol] : [];
  });

  /** El logo solo es clickeable si el rol tiene alguna pantalla propia
   * (evita mandar a un Cliente a `/dashboard`, que su roleGuard rebota). */
  logoPath = computed<string | null>(() => this.navItems()[0]?.path ?? null);

  toggle(): void {
    this.open.update((v) => !v);
  }
}
