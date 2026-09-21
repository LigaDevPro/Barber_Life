import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { BarberoDetail, BarberoMe, BarberoPublic } from '../models/models';

@Injectable({ providedIn: 'root' })
export class BarberoService {
  constructor(private http: HttpClient) {}

  listar(): Observable<BarberoPublic[]> {
    return this.http.get<BarberoPublic[]>(`${environment.apiUrl}/barberos/`);
  }

  detalle(id: number): Observable<BarberoDetail> {
    return this.http.get<BarberoDetail>(`${environment.apiUrl}/barberos/${id}/`);
  }

  getMe(): Observable<BarberoMe> {
    return this.http.get<BarberoMe>(`${environment.apiUrl}/barberos/me/`);
  }

  actualizarMe(payload: Partial<Pick<BarberoMe, 'foto_perfil_url'>>): Observable<BarberoMe> {
    return this.http.patch<BarberoMe>(`${environment.apiUrl}/barberos/me/`, payload);
  }
}
