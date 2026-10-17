import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { LogoComponent } from '../../../shared/logo/logo.component';
import { AuthHeroComponent } from '../../../shared/auth-hero/auth-hero.component';
import { GoogleButtonComponent } from '../../../shared/google-button/google-button.component';
import { GoogleAuthService } from '../../../core/auth/google-auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, LogoComponent, AuthHeroComponent, GoogleButtonComponent],
  templateUrl: './login.component.html',
})
export class LoginComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  googleHabilitado = inject(GoogleAuthService).habilitado;

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  loading = signal(false);
  errorMsg = signal<string | null>(null);
  sinAcceso = signal(false);

  ngOnInit(): void {
    this.sinAcceso.set(this.route.snapshot.queryParamMap.get('sinAcceso') === '1');
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.errorMsg.set(null);

    const { email, password } = this.form.getRawValue();
    this.authService.login(email!, password!).subscribe({
      next: (res) => {
        this.loading.set(false);
        const destino = res.usuario.rol === 'cliente' ? '/inicio' : '/dashboard';
        this.router.navigate([destino]);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.non_field_errors?.[0] || 'Email o contraseña incorrectos.');
      },
    });
  }

  /** Google ya autenticó a la persona: el backend valida el ID token y devuelve nuestra sesión. */
  entrarConGoogle(credencial: string): void {
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
          err?.error?.non_field_errors?.[0] || err?.error?.detail || 'No se pudo iniciar sesión con Google.',
        );
      },
    });
  }

  googleNoDisponible(): void {
    this.errorMsg.set('No se pudo cargar el acceso con Google. Probá de nuevo más tarde.');
  }
}
