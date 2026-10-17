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

  /** Foto de perfil del barbero (se sube a la API, ya no se pega una URL). */
  fotoUrl = signal('');
  subiendoFoto = signal(false);
  readonly formatosFoto = ['image/jpeg', 'image/png', 'image/webp'];
  readonly maxFotoMb = 2;

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
          this.fotoUrl.set(b.foto_perfil_url);
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

  /** Valida en el cliente (tipo y peso) y sube la foto; el backend vuelve a validar. */
  elegirFoto(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = ''; // permite volver a elegir el mismo archivo
    if (!archivo) return;
    this.errorMsg.set(null);
    this.successMsg.set(null);
    if (!this.formatosFoto.includes(archivo.type)) {
      this.errorMsg.set('Elegí una imagen JPEG, PNG o WebP.');
      return;
    }
    if (archivo.size > this.maxFotoMb * 1024 * 1024) {
      this.errorMsg.set(`La imagen no puede pesar más de ${this.maxFotoMb} MB.`);
      return;
    }
    this.subiendoFoto.set(true);
    this.barberoService.subirFoto(archivo).subscribe({
      next: (b) => {
        this.fotoUrl.set(b.foto_perfil_url);
        this.subiendoFoto.set(false);
        this.successMsg.set('Foto actualizada.');
      },
      error: (err) => {
        this.subiendoFoto.set(false);
        this.errorMsg.set(err?.error?.foto?.[0] || err?.error?.detail || 'No se pudo subir la foto.');
      },
    });
  }

  quitarFoto(): void {
    this.subiendoFoto.set(true);
    this.errorMsg.set(null);
    this.successMsg.set(null);
    this.barberoService.quitarFoto().subscribe({
      next: () => {
        this.fotoUrl.set('');
        this.subiendoFoto.set(false);
        this.successMsg.set('Foto eliminada.');
      },
      error: () => {
        this.subiendoFoto.set(false);
        this.errorMsg.set('No se pudo quitar la foto.');
      },
    });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
