import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Pagina, TurnoResumen } from '../models/models';

export interface TurnoCreatePayload {
  barbero: number;
  servicio: number;
  fecha_turno: string;
  hora_inicio: string;
  observaciones?: string;
}

@Injectable({ providedIn: 'root' })
export class TurnoService {
  constructor(private http: HttpClient) {}

  /** POST /api/turnos/ — reserva hecha por el cliente. */
  crear(payload: TurnoCreatePayload): Observable<TurnoResumen> {
    return this.http.post<TurnoResumen>(`${environment.apiUrl}/turnos/`, payload);
  }

  /** GET /api/turnos/mis-turnos/?page=&estado= — turnos propios del cliente. */
  misTurnos(page = 1, estado = ''): Observable<Pagina<TurnoResumen>> {
    let params = new HttpParams().set('page', page);
    if (estado) params = params.set('estado', estado);
    return this.http.get<Pagina<TurnoResumen>>(`${environment.apiUrl}/turnos/mis-turnos/`, { params });
  }

  /** PATCH /api/turnos/<id>/cancelar/ — cancela un turno propio (ventana de 2hs). */
  cancelar(id: number): Observable<TurnoResumen> {
    return this.http.patch<TurnoResumen>(`${environment.apiUrl}/turnos/${id}/cancelar/`, {});
  }
}
