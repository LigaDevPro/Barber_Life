import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

type Resultado = 'exito' | 'fallo' | 'pendiente';

interface Contenido {
  titulo: string;
  mensaje: string;
  clasesTitulo: string;
}

const CONTENIDO: Record<Resultado, Contenido> = {
  exito: {
    titulo: '¡Pago aprobado!',
    mensaje:
      'Recibimos tu pago. Tu turno se confirma en unos instantes: lo vas a ver como "confirmado" en Mis turnos.',
    clasesTitulo: 'text-bl-success',
  },
  pendiente: {
    titulo: 'Pago pendiente',
    mensaje:
      'Mercado Pago todavía está procesando tu pago. Cuando se acredite, tu turno pasa a "confirmado" automáticamente.',
    clasesTitulo: 'text-bl-warning',
  },
  fallo: {
    titulo: 'No se pudo completar el pago',
    mensaje:
      'El pago no se realizó y la reserva puede haberse cancelado. Podés revisar el estado en Mis turnos o volver a reservar.',
    clasesTitulo: 'text-bl-danger-text',
  },
};

/** Pantalla a la que vuelve el usuario desde Mercado Pago (back_urls de la
 * preferencia, ver backend/gestion/mercadopago_client.py). El resultado
 * viaja en `?estado=exito|fallo|pendiente`. No confía en esto para nada
 * sensible: el estado real del turno lo confirma el webhook del backend, acá
 * solo se informa al usuario. */
@Component({
  selector: 'app-pago-resultado',
  standalone: true,
  imports: [CommonModule, RouterLink, TopbarComponent],
  templateUrl: './pago-resultado.component.html',
})
export class PagoResultadoComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  authService = inject(AuthService);

  resultado = signal<Resultado>('pendiente');

  get contenido(): Contenido {
    return CONTENIDO[this.resultado()];
  }

  ngOnInit(): void {
    const estado = this.route.snapshot.queryParamMap.get('estado');
    // Un valor desconocido o ausente se trata como pendiente: es el mensaje
    // más neutro (no afirma ni que pagó ni que falló).
    this.resultado.set(estado === 'exito' || estado === 'fallo' ? estado : 'pendiente');
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
