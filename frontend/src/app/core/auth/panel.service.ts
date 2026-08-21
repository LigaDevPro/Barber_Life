import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DashboardData, ServicioMasSolicitado, TurnosPage } from '../models/models';

@Injectable({ providedIn: 'root' })
export class PanelService {
  constructor(private http: HttpClient) {}

  getDashboard(): Observable<DashboardData> {
    return this.http.get<DashboardData>(`${environment.apiUrl}/dashboard/`);
  }

  getTurnos(page: number, q = '', estado = ''): Observable<TurnosPage> {
    let params = new HttpParams().set('page', page);
    if (q) params = params.set('q', q);
    if (estado) params = params.set('estado', estado);
    return this.http.get<TurnosPage>(`${environment.apiUrl}/turnos/`, { params });
  }

  getServiciosMasSolicitados(): Observable<ServicioMasSolicitado[]> {
    return this.http.get<ServicioMasSolicitado[]>(`${environment.apiUrl}/turnos/servicios-mas-solicitados/`);
  }

  actualizarEstadoTurno(id: number, estado: string): Observable<unknown> {
    return this.http.patch(`${environment.apiUrl}/turnos/${id}/`, { estado });
  }
}
