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
  {
    path: 'perfil',
    loadComponent: () => import('./features/perfil/perfil.component').then((m) => m.PerfilComponent),
    canActivate: [authGuard, roleGuard(['cliente', 'barbero'])],
  },
  {
    path: 'inicio',
    loadComponent: () => import('./features/inicio/inicio.component').then((m) => m.InicioComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'solicitar-turno',
    loadComponent: () =>
      import('./features/solicitar-turno/solicitar-turno.component').then((m) => m.SolicitarTurnoComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'mis-turnos',
    loadComponent: () => import('./features/mis-turnos/mis-turnos.component').then((m) => m.MisTurnosComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'catalogo',
    loadComponent: () => import('./features/catalogo/catalogo.component').then((m) => m.CatalogoComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  {
    path: 'notificaciones',
    loadComponent: () =>
      import('./features/notificaciones/notificaciones.component').then((m) => m.NotificacionesComponent),
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: 'login' },
];
