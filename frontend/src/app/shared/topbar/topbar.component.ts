import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LogoComponent } from '../logo/logo.component';

@Component({
  selector: 'bl-topbar',
  standalone: true,
  imports: [CommonModule, RouterLink, LogoComponent],
  template: `
    <header class="topbar">
      <a routerLink="/dashboard" class="topbar-brand">
        <bl-logo [size]="28" />
        <span>Barber Life</span>
      </a>

      <button class="topbar-menu-btn" type="button" (click)="toggle()" aria-label="Menú">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M2 5h16M2 10h16M2 15h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        </svg>
      </button>

      @if (open()) {
        <nav class="topbar-dropdown">
          <a routerLink="/dashboard" (click)="open.set(false)">Dashboard</a>
          <a routerLink="/turnos" (click)="open.set(false)">Gestión de turnos</a>
          <button type="button" (click)="logout.emit()">Cerrar sesión</button>
        </nav>
      }
    </header>
  `,
  styleUrl: './topbar.component.scss',
})
export class TopbarComponent {
  @Output() logout = new EventEmitter<void>();
  open = signal(false);

  toggle(): void {
    this.open.update((v) => !v);
  }
}
