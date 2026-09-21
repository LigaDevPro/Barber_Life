import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { ClienteService } from '../../core/services/cliente.service';
import { BarberoService } from '../../core/services/barbero.service';
import { TopbarComponent } from '../../shared/topbar/topbar.component';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TopbarComponent],
  templateUrl: './perfil.component.html',
})
export class PerfilComponent implements OnInit {
  private fb = inject(FormBuilder);
  private clienteService = inject(ClienteService);
  private barberoService = inject(BarberoService);
  private router = inject(Router);
  authService = inject(AuthService);

  loading = signal(true);
  guardando = signal(false);
  errorMsg = signal<string | null>(null);
  successMsg = signal<string | null>(null);

  esCliente = computed(() => this.authService.currentUser()?.rol === 'cliente');
  esBarbero = computed(() => this.authService.currentUser()?.rol === 'barbero');

  clienteForm = this.fb.group({
    telefono: [''],
    fecha_nacimiento: [''],
  });

  barberoForm = this.fb.group({
    foto_perfil_url: [''],
  });

  ngOnInit(): void {
    if (this.esCliente()) {
      this.clienteService.getMe().subscribe({
        next: (c) => {
          this.clienteForm.patchValue({
            telefono: c.telefono,
            fecha_nacimiento: c.fecha_nacimiento ?? '',
          });
          this.loading.set(false);
        },
        error: () => {
          this.errorMsg.set('No se pudo cargar tu perfil.');
          this.loading.set(false);
        },
      });
    } else if (this.esBarbero()) {
      this.barberoService.getMe().subscribe({
        next: (b) => {
          this.barberoForm.patchValue({ foto_perfil_url: b.foto_perfil_url });
          this.loading.set(false);
        },
        error: () => {
          this.errorMsg.set('No se pudo cargar tu perfil.');
          this.loading.set(false);
        },
      });
    } else {
      this.loading.set(false);
    }
  }

  guardarCliente(): void {
    this.guardando.set(true);
    this.errorMsg.set(null);
    this.successMsg.set(null);
    const { telefono, fecha_nacimiento } = this.clienteForm.getRawValue();
    this.clienteService
      .actualizarMe({ telefono: telefono ?? '', fecha_nacimiento: fecha_nacimiento || null })
      .subscribe({
        next: () => {
          this.guardando.set(false);
          this.successMsg.set('Perfil actualizado.');
        },
        error: (err) => {
          this.guardando.set(false);
          this.errorMsg.set(err?.error?.detail || 'No se pudo actualizar tu perfil.');
        },
      });
  }

  guardarBarbero(): void {
    this.guardando.set(true);
    this.errorMsg.set(null);
    this.successMsg.set(null);
    const { foto_perfil_url } = this.barberoForm.getRawValue();
    this.barberoService.actualizarMe({ foto_perfil_url: foto_perfil_url ?? '' }).subscribe({
      next: () => {
        this.guardando.set(false);
        this.successMsg.set('Perfil actualizado.');
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorMsg.set(err?.error?.detail || 'No se pudo actualizar tu perfil.');
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
