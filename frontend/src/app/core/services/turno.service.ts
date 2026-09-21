import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TurnoResumen } from '../models/models';

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
}
