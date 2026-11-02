import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { LogoComponent } from '../../../shared/logo/logo.component';
import { AuthHeroComponent } from '../../../shared/auth-hero/auth-hero.component';

/** US05 — Pedir el enlace para restablecer la contraseña. */
@Component({
  selector: 'app-recuperar-contrasena',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, LogoComponent, AuthHeroComponent],
  templateUrl: './recuperar-contrasena.component.html',
})
export class RecuperarContrasenaComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
  });

  loading = signal(false);
  errorMsg = signal<string | null>(null);
  enviado = signal<string | null>(null);

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.errorMsg.set(null);
    this.authService.solicitarRecuperacion(this.form.getRawValue().email!).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.enviado.set(res.detail);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.email?.[0] || 'No se pudo enviar el enlace. Intentá de nuevo.');
      },
    });
  }
}
