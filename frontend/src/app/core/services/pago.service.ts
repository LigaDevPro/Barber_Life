import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Pago, PagoCreateResponse } from '../models/models';

@Injectable({ providedIn: 'root' })
export class PagoService {
  constructor(private http: HttpClient) {}

  /** GET /api/pagos/ — el cliente ve los propios, el admin ve todos. Sin
   * paginar (pagination_class = None en el backend). */
  listar(): Observable<Pago[]> {
    return this.http.get<Pago[]>(`${environment.apiUrl}/pagos/`);
  }

  /** POST /api/pagos/ — genera el Pago y la preferencia de Mercado Pago
   * para un turno propio en estado pendiente. Redirigir a `init_point`. */
  crear(turnoId: number): Observable<PagoCreateResponse> {
    return this.http.post<PagoCreateResponse>(`${environment.apiUrl}/pagos/`, { turno: turnoId });
  }
}
