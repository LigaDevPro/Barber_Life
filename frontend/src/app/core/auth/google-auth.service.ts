import { Injectable, NgZone, inject } from '@angular/core';
import { environment } from '../../../environments/environment';

const SCRIPT_URL = 'https://accounts.google.com/gsi/client';

/** Lo mínimo que usamos de Google Identity Services (https://accounts.google.com/gsi/client). */
interface GoogleIdentity {
  accounts: {
    id: {
      initialize(config: { client_id: string; callback: (res: { credential: string }) => void }): void;
      renderButton(el: HTMLElement, opciones: Record<string, unknown>): void;
    };
  };
}

/**
 * "Iniciar sesión con Google" (OAuth 2.0 / OpenID Connect con Google Identity Services).
 * Carga el script de Google una sola vez y dibuja el botón oficial; cuando el usuario
 * elige su cuenta Google entrega un ID token que el backend valida en /api/auth/google/.
 */
@Injectable({ providedIn: 'root' })
export class GoogleAuthService {
  private zone = inject(NgZone);
  private script: Promise<GoogleIdentity> | null = null;

  get habilitado(): boolean {
    return !!environment.googleClientId;
  }

  private cargarScript(): Promise<GoogleIdentity> {
    this.script ??= new Promise<GoogleIdentity>((resolve, reject) => {
      const existente = (window as unknown as { google?: GoogleIdentity }).google;
      if (existente?.accounts?.id) return resolve(existente);
      const tag = document.createElement('script');
      tag.src = SCRIPT_URL;
      tag.async = true;
      tag.onload = () => resolve((window as unknown as { google: GoogleIdentity }).google);
      tag.onerror = () => {
        this.script = null; // permite reintentar
        reject(new Error('No se pudo cargar Google'));
      };
      document.head.appendChild(tag);
    });
    return this.script;
  }

  async renderizarBoton(
    contenedor: HTMLElement,
    texto: 'signin_with' | 'signup_with',
    alRecibirCredencial: (credencial: string) => void,
  ): Promise<void> {
    const google = await this.cargarScript();
    google.accounts.id.initialize({
      client_id: environment.googleClientId,
      // El callback llega fuera de Angular: se vuelve a la zona para que la vista se actualice.
      callback: (res) => this.zone.run(() => alRecibirCredencial(res.credential)),
    });
    google.accounts.id.renderButton(contenedor, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: texto,
      shape: 'rectangular',
      locale: 'es',
      width: Math.min(400, contenedor.clientWidth || 320),
    });
  }
}
