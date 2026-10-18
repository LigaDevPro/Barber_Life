import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
  AbstractControl,
  ValidationErrors,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { LogoComponent } from '../../../shared/logo/logo.component';
import { AuthHeroComponent } from '../../../shared/auth-hero/auth-hero.component';
import { GoogleButtonComponent } from '../../../shared/google-button/google-button.component';
import { GoogleAuthService } from '../../../core/auth/google-auth.service';

function passwordsMatch(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password')?.value;
  const confirm = control.get('passwordConfirm')?.value;
  return password && confirm && password !== confirm ? { mismatch: true } : null;
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, LogoComponent, AuthHeroComponent, GoogleButtonComponent],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  googleHabilitado = inject(GoogleAuthService).habilitado;

  form = this.fb.group(
    {
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      passwordConfirm: ['', [Validators.required]],
    },
    { validators: passwordsMatch },
  );

  loading = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.errorMsg.set(null);

    const { email, password, passwordConfirm } = this.form.getRawValue();
    this.authService.register(email!, password!, passwordConfirm!).subscribe({
      next: () => {
        this.loading.set(false);
        this.successMsg.set('Cuenta creada. Redirigiendo al inicio de sesión...');
        setTimeout(() => this.router.navigate(['/login']), 1200);
      },
      error: (err) => {
        this.loading.set(false);
        const data = err?.error || {};
        const firstError =
          data.email?.[0] || data.password?.[0] || data.password_confirm?.[0] || data.detail;
        this.errorMsg.set(firstError || 'No se pudo crear la cuenta. Intentá de nuevo.');
      },
    });
  }

  /** Registrarse con Google = crear la cuenta (si no existe) e iniciar sesión directamente. */
  registrarConGoogle(credencial: string): void {
    this.loading.set(true);
    this.errorMsg.set(null);
    this.authService.loginConGoogle(credencial).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.router.navigate([res.usuario.rol === 'cliente' ? '/inicio' : '/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(
          err?.error?.non_field_errors?.[0] || err?.error?.detail || 'No se pudo continuar con Google.',
        );
      },
    });
  }

  googleNoDisponible(): void {
    this.errorMsg.set('No se pudo cargar el acceso con Google. Probá de nuevo más tarde.');
  }
}
