import { Injectable, effect, inject, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from '../auth/auth.service';
import { Notificacion } from '../models/models';

const PING_MS = 30_000;
const ESPERA_MAX_MS = 30_000;

/**
 * Notificaciones en tiempo real por WebSocket (ws://.../ws/notificaciones/).
 *
 * - Se conecta solo cuando hay sesión y se desconecta al cerrarla.
 * - Se autentica con el primer mensaje {type:'auth', token} (el token no viaja en la URL).
 * - Si se corta, reintenta con espera creciente (1s, 2s, 4s... hasta 30s).
 * - Cada notificación nueva sale por `nueva$`.
 */
@Injectable({ providedIn: 'root' })
export class NotificacionesTiempoRealService {
  private auth = inject(AuthService);

  /** true cuando el servidor confirmó la autenticación. */
  readonly conectado = signal(false);
  readonly nueva$ = new Subject<Notificacion>();

  private socket: WebSocket | null = null;
  private temporizadorReintento: ReturnType<typeof setTimeout> | null = null;
  private temporizadorPing: ReturnType<typeof setInterval> | null = null;
  private intentos = 0;

  constructor() {
    effect(() => {
      if (this.auth.currentUser()) this.conectar();
      else this.desconectar();
    });
  }

  private conectar(): void {
    if (this.socket || typeof WebSocket === 'undefined') return;
    const token = this.auth.getAccessToken();
    if (!token) return;

    const socket = new WebSocket(`${environment.wsUrl}notificaciones/`);
    this.socket = socket;

    socket.onopen = () => socket.send(JSON.stringify({ type: 'auth', token }));

    socket.onmessage = (evento: MessageEvent) => {
      let mensaje: { type?: string; data?: Notificacion };
      try {
        mensaje = JSON.parse(evento.data);
      } catch {
        return;
      }
      if (mensaje.type === 'auth_ok') {
        this.conectado.set(true);
        this.intentos = 0;
        this.iniciarPing(socket);
      } else if (mensaje.type === 'notificacion' && mensaje.data) {
        this.nueva$.next(mensaje.data);
      }
    };

    socket.onclose = () => {
      if (this.socket !== socket) return; // lo cerramos nosotros (logout) o ya hay otro
      this.socket = null;
      this.conectado.set(false);
      this.detenerPing();
      if (this.auth.currentUser()) this.programarReintento();
    };
  }

  private programarReintento(): void {
    const espera = Math.min(ESPERA_MAX_MS, 1000 * 2 ** this.intentos);
    this.intentos++;
    this.temporizadorReintento = setTimeout(() => {
      this.temporizadorReintento = null;
      this.conectar();
    }, espera);
  }

  private iniciarPing(socket: WebSocket): void {
    this.detenerPing();
    this.temporizadorPing = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
    }, PING_MS);
  }

  private detenerPing(): void {
    if (this.temporizadorPing) clearInterval(this.temporizadorPing);
    this.temporizadorPing = null;
  }

  private desconectar(): void {
    if (this.temporizadorReintento) clearTimeout(this.temporizadorReintento);
    this.temporizadorReintento = null;
    this.detenerPing();
    this.intentos = 0;
    const socket = this.socket;
    this.socket = null;
    this.conectado.set(false);
    socket?.close(1000);
  }
}
