import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  {
    path: 'login',
    title: 'Iniciar sesión | Barber Life',
    loadComponent: () => import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    title: 'Crear cuenta | Barber Life',
    loadComponent: () => import('./features/auth/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'dashboard',
    title: 'Dashboard | Barber Life',
    loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  {
    path: 'turnos',
    title: 'Gestión de turnos | Barber Life',
    loadComponent: () => import('./features/turnos/turnos.component').then((m) => m.TurnosComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  {
    path: 'perfil',
    title: 'Mi perfil | Barber Life',
    loadComponent: () => import('./features/perfil/perfil.component').then((m) => m.PerfilComponent),
    canActivate: [authGuard, roleGuard(['cliente', 'barbero'])],
  },
  {
    path: 'inicio',
    title: 'Inicio | Barber Life',
    loadComponent: () => import('./features/inicio/inicio.component').then((m) => m.InicioComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'solicitar-turno',
    title: 'Solicitar turno | Barber Life',
    loadComponent: () =>
      import('./features/solicitar-turno/solicitar-turno.component').then((m) => m.SolicitarTurnoComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'mis-turnos',
    title: 'Mis turnos | Barber Life',
    loadComponent: () => import('./features/mis-turnos/mis-turnos.component').then((m) => m.MisTurnosComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'pago/resultado',
    title: 'Resultado del pago | Barber Life',
    loadComponent: () =>
      import('./features/pago-resultado/pago-resultado.component').then((m) => m.PagoResultadoComponent),
    canActivate: [authGuard, roleGuard(['cliente'])],
  },
  {
    path: 'catalogo',
    title: 'Catálogo | Barber Life',
    loadComponent: () => import('./features/catalogo/catalogo.component').then((m) => m.CatalogoComponent),
    canActivate: [authGuard, roleGuard(['barbero', 'admin'])],
  },
  {
    path: 'notificaciones',
    title: 'Notificaciones | Barber Life',
    loadComponent: () =>
      import('./features/notificaciones/notificaciones.component').then((m) => m.NotificacionesComponent),
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: 'login' },
];
