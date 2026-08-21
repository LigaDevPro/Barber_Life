import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { PanelService } from '../../core/auth/panel.service';
import { AuthService } from '../../core/auth/auth.service';
import { DashboardData } from '../../core/models/models';
import { LogoComponent } from '../../shared/logo/logo.component';
import { TopbarComponent } from '../../shared/topbar/topbar.component';
import { WeekChartComponent } from '../../shared/week-chart/week-chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, LogoComponent, TopbarComponent, WeekChartComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  data = signal<DashboardData | null>(null);
  loading = signal(true);
  errorMsg = signal<string | null>(null);

  constructor(private panelService: PanelService, public authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading.set(true);
    this.errorMsg.set(null);
    this.panelService.getDashboard().subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudo cargar el dashboard.');
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
