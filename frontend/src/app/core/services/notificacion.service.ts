import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Notificacion, Pagina } from '../models/models';

@Injectable({ providedIn: 'root' })
export class NotificacionService {
  constructor(private http: HttpClient) {}

  /** GET /api/notificaciones/?leida=&page= — propias, paginadas a nivel de
   * Mongo (skip/limit). `leida` es opcional: sin filtro trae todas. */
  listar(page = 1, leida?: boolean): Observable<Pagina<Notificacion>> {
    let params = new HttpParams().set('page', page);
    if (leida !== undefined) params = params.set('leida', String(leida));
    return this.http.get<Pagina<Notificacion>>(`${environment.apiUrl}/notificaciones/`, { params });
  }

  marcarLeida(id: string): Observable<Notificacion> {
    return this.http.patch<Notificacion>(`${environment.apiUrl}/notificaciones/${id}/leida/`, {});
  }
}
