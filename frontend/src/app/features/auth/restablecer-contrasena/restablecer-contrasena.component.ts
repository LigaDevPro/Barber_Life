import { Component, OnInit, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { LogoComponent } from '../../../shared/logo/logo.component';
import { AuthHeroComponent } from '../../../shared/auth-hero/auth-hero.component';

function passwordsMatch(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password')?.value;
  const confirm = control.get('passwordConfirm')?.value;
  return password && confirm && password !== confirm ? { mismatch: true } : null;
}

/** US05 — Elegir la contraseña nueva desde el enlace del mail (?uid=...&token=...). */
@Component({
  selector: 'app-restablecer-contrasena',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, LogoComponent, AuthHeroComponent],
  templateUrl: './restablecer-contrasena.component.html',
})
export class RestablecerContrasenaComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  form = this.fb.group(
    {
      password: ['', [Validators.required, Validators.minLength(8)]],
      passwordConfirm: ['', [Validators.required]],
    },
    { validators: passwordsMatch },
  );

  uid = '';
  token = '';
  loading = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    this.uid = params.get('uid') ?? '';
    this.token = params.get('token') ?? '';
    if (!this.uid || !this.token) {
      this.errorMsg.set('El enlace no es válido o ya venció. Pedí uno nuevo.');
    }
  }

  submit(): void {
    if (this.form.invalid || !this.uid || !this.token) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.errorMsg.set(null);
    const { password, passwordConfirm } = this.form.getRawValue();
    this.authService.restablecerContrasena(this.uid, this.token, password!, passwordConfirm!).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.successMsg.set(res.detail);
        setTimeout(() => this.router.navigate(['/login']), 1500);
      },
      error: (err) => {
        this.loading.set(false);
        const data = err?.error || {};
        this.errorMsg.set(
          data.non_field_errors?.[0] ||
            data.password?.[0] ||
            data.password_confirm?.[0] ||
            'No se pudo cambiar la contraseña. Intentá de nuevo.',
        );
      },
    });
  }
}
