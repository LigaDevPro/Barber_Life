import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LogoComponent } from '../logo/logo.component';

@Component({
  selector: 'bl-topbar',
  standalone: true,
  imports: [CommonModule, RouterLink, LogoComponent],
  template: `
    <header class="relative flex items-center justify-between border-b border-bl-border px-5 py-4">
      <a
        routerLink="/dashboard"
        class="flex items-center gap-2 text-[15px] font-bold text-bl-text no-underline"
      >
        <bl-logo [size]="28" />
        <span>Barber Life</span>
      </a>

      <button
        class="flex cursor-pointer rounded-field border border-bl-border bg-transparent p-2 text-bl-text hover:bg-bl-surface-2"
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
          <a
            routerLink="/dashboard"
            (click)="open.set(false)"
            class="border-b border-bl-border px-4 py-3 text-left text-[13.5px] text-bl-text no-underline hover:bg-bl-surface-2"
          >
            Dashboard
          </a>
          <a
            routerLink="/turnos"
            (click)="open.set(false)"
            class="border-b border-bl-border px-4 py-3 text-left text-[13.5px] text-bl-text no-underline hover:bg-bl-surface-2"
          >
            Gestión de turnos
          </a>
          <button
            type="button"
            (click)="logout.emit()"
            class="cursor-pointer border-0 bg-transparent px-4 py-3 text-left text-[13.5px] text-bl-danger hover:bg-bl-surface-2"
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

  toggle(): void {
    this.open.update((v) => !v);
  }
}
