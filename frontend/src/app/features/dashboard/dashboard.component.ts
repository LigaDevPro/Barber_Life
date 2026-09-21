import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { PanelService } from '../../core/auth/panel.service';
import { DashboardData } from '../../core/models/models';
import { TopbarComponent } from '../../shared/topbar/topbar.component';
import { WeekChartComponent } from '../../shared/week-chart/week-chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TopbarComponent,
    WeekChartComponent,
  ],
  templateUrl: './dashboard.component.html',
})

export class DashboardComponent implements OnInit {
  private readonly panelService = inject(PanelService);
  private readonly router = inject(Router);

  readonly authService = inject(AuthService);

  readonly data = signal<DashboardData | null>(null);
  readonly loading = signal(true);
  readonly errorMsg = signal<string | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    this.panelService.getDashboard().subscribe({
      next: (data) => {
        this.data.set(data);
        this.loading.set(false);
      },

      error: (error) => {
        console.error('Error al cargar el dashboard:', error);

        this.loading.set(false);

        this.errorMsg.set(
          error?.error?.detail ??
            'No se pudo cargar el dashboard.'
        );
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}