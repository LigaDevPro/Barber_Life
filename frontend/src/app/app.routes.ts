import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  {
    path: 'turnos',
    loadComponent: () => import('./features/turnos/turnos.component').then((m) => m.TurnosComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  { path: '**', redirectTo: 'login' },
];
