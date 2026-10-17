import { AfterViewInit, Component, ElementRef, EventEmitter, Input, Output, ViewChild, inject } from '@angular/core';
import { GoogleAuthService } from '../../core/auth/google-auth.service';

/** Botón oficial de Google. Emite el ID token (`credencial`) cuando el usuario elige su cuenta. */
@Component({
  selector: 'bl-google-button',
  standalone: true,
  template: `<div #contenedor class="flex w-full justify-center" data-testid="google-button"></div>`,
})
export class GoogleButtonComponent implements AfterViewInit {
  @Input() texto: 'signin_with' | 'signup_with' = 'signin_with';
  @Output() credencial = new EventEmitter<string>();
  @Output() fallo = new EventEmitter<void>();
  @ViewChild('contenedor', { static: true }) contenedor!: ElementRef<HTMLElement>;

  private google = inject(GoogleAuthService);

  ngAfterViewInit(): void {
    this.google
      .renderizarBoton(this.contenedor.nativeElement, this.texto, (c) => this.credencial.emit(c))
      .catch(() => this.fallo.emit());
  }
}
