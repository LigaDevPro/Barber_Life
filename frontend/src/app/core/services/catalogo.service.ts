import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { BarberoServicio, Horario, Servicio } from '../models/models';

/**
 * Agrupa Servicio, Horario y BarberoServicio — mismo agrupamiento que ya usa
 * el backend en `serializers/catalogo.py` / `urls/catalogo.py` / `views/catalogo.py`.
 * Los tres tienen soft delete (`activo=False`, no DELETE real).
 */
@Injectable({ providedIn: 'root' })
export class CatalogoService {
  constructor(private http: HttpClient) {}

  // --- Servicio ---

  listarServicios(): Observable<Servicio[]> {
    return this.http.get<Servicio[]>(`${environment.apiUrl}/servicios/`);
  }

  obtenerServicio(id: number): Observable<Servicio> {
    return this.http.get<Servicio>(`${environment.apiUrl}/servicios/${id}/`);
  }

  crearServicio(payload: Omit<Servicio, 'id' | 'activo'>): Observable<Servicio> {
    return this.http.post<Servicio>(`${environment.apiUrl}/servicios/`, payload);
  }

  actualizarServicio(id: number, payload: Partial<Servicio>): Observable<Servicio> {
    return this.http.patch<Servicio>(`${environment.apiUrl}/servicios/${id}/`, payload);
  }

  desactivarServicio(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/servicios/${id}/`);
  }

  // --- Horario ---

  listarHorarios(barberoId?: number): Observable<Horario[]> {
    let params = new HttpParams();
    if (barberoId) params = params.set('barbero', barberoId);
    return this.http.get<Horario[]>(`${environment.apiUrl}/horarios/`, { params });
  }

  crearHorario(payload: Omit<Horario, 'id' | 'dia_semana_display' | 'activo'>): Observable<Horario> {
    return this.http.post<Horario>(`${environment.apiUrl}/horarios/`, payload);
  }

  actualizarHorario(id: number, payload: Partial<Horario>): Observable<Horario> {
    return this.http.patch<Horario>(`${environment.apiUrl}/horarios/${id}/`, payload);
  }

  desactivarHorario(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/horarios/${id}/`);
  }

  // --- BarberoServicio ---

  listarBarberoServicio(barberoId?: number): Observable<BarberoServicio[]> {
    let params = new HttpParams();
    if (barberoId) params = params.set('barbero', barberoId);
    return this.http.get<BarberoServicio[]>(`${environment.apiUrl}/barbero-servicio/`, { params });
  }

  crearBarberoServicio(
    payload: Omit<BarberoServicio, 'id' | 'servicio_nombre' | 'precio' | 'activo' | 'fecha_creacion'>,
  ): Observable<BarberoServicio> {
    return this.http.post<BarberoServicio>(`${environment.apiUrl}/barbero-servicio/`, payload);
  }

  actualizarBarberoServicio(id: number, payload: Partial<BarberoServicio>): Observable<BarberoServicio> {
    return this.http.patch<BarberoServicio>(`${environment.apiUrl}/barbero-servicio/${id}/`, payload);
  }

  desactivarBarberoServicio(id: number): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/barbero-servicio/${id}/`);
  }
}
