import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DashboardData, ServicioMasSolicitado, TurnosPage } from '../models/models';

/** Filtros combinables de la agenda: texto + estado + rango de fechas (AAAA-MM-DD, inclusivo). */
export interface FiltrosTurnos {
  q?: string;
  estado?: string;
  fechaDesde?: string;
  fechaHasta?: string;
}

@Injectable({ providedIn: 'root' })
export class PanelService {
  constructor(private http: HttpClient) {}

  getDashboard(): Observable<DashboardData> {
    return this.http.get<DashboardData>(`${environment.apiUrl}/dashboard/`);
  }

  private paramsTurnos(filtros: FiltrosTurnos, page?: number): HttpParams {
    let params = new HttpParams();
    if (page) params = params.set('page', page);
    if (filtros.q) params = params.set('q', filtros.q);
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.fechaDesde) params = params.set('fecha_desde', filtros.fechaDesde);
    if (filtros.fechaHasta) params = params.set('fecha_hasta', filtros.fechaHasta);
    return params;
  }

  /** GET /api/turnos/?page=&q=&estado=&fecha_desde=&fecha_hasta= */
  getTurnos(page: number, filtros: FiltrosTurnos = {}): Observable<TurnosPage> {
    return this.http.get<TurnosPage>(`${environment.apiUrl}/turnos/`, {
      params: this.paramsTurnos(filtros, page),
    });
  }

  /** GET /api/turnos/exportar/ — CSV con los mismos filtros que el listado. */
  exportarTurnos(filtros: FiltrosTurnos = {}): Observable<Blob> {
    return this.http.get(`${environment.apiUrl}/turnos/exportar/`, {
      params: this.paramsTurnos(filtros),
      responseType: 'blob',
    });
  }

  getServiciosMasSolicitados(): Observable<ServicioMasSolicitado[]> {
    return this.http.get<ServicioMasSolicitado[]>(`${environment.apiUrl}/turnos/servicios-mas-solicitados/`);
  }

  actualizarEstadoTurno(id: number, estado: string): Observable<unknown> {
    return this.http.patch(`${environment.apiUrl}/turnos/${id}/`, { estado });
  }
}
