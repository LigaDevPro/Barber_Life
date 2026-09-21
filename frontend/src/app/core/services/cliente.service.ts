import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Cliente } from '../models/models';

@Injectable({ providedIn: 'root' })
export class ClienteService {
  constructor(private http: HttpClient) {}

  getMe(): Observable<Cliente> {
    return this.http.get<Cliente>(`${environment.apiUrl}/clientes/me/`);
  }

  actualizarMe(payload: Partial<Pick<Cliente, 'fecha_nacimiento' | 'telefono'>>): Observable<Cliente> {
    return this.http.patch<Cliente>(`${environment.apiUrl}/clientes/me/`, payload);
  }
}
