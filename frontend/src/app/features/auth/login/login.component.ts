import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { LogoComponent } from '../../../shared/logo/logo.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, LogoComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

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
        if (res.usuario.rol === 'admin' || res.usuario.rol === 'barbero') {
          this.router.navigate(['/dashboard']);
        } else {
          this.router.navigate(['/login'], { queryParams: { sinAcceso: '1' } });
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set(err?.error?.non_field_errors?.[0] || 'Email o contraseña incorrectos.');
      },
    });
  }
}