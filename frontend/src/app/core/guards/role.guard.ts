import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';
import { Rol } from '../models/models';

/**
 * Restringe rutas según rol, respetando la Matriz de Control de Acceso de la
 * wiki (ESTRUCTURA-Y-ARQUITECTURA > RBAC). Dashboard y Gestión de Turnos son
 * exclusivos de Barbero/Administrador en este sprint — un Cliente que intenta
 * entrar es redirigido con un mensaje, no simplemente bloqueado en silencio.
 */
export function roleGuard(rolesPermitidos: Rol[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    const usuario = auth.currentUser();
    if (!usuario) {
      router.navigate(['/login']);
      return false;
    }
    if (!rolesPermitidos.includes(usuario.rol)) {
      router.navigate(['/login'], { queryParams: { sinAcceso: '1' } });
      return false;
    }
    return true;
  };
}
