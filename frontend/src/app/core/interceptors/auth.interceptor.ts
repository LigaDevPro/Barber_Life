import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../auth/auth.service';
import { environment } from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const http = inject(HttpClient);
  const router = inject(Router);

  const token = auth.getAccessToken();
  const authReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      const refresh = auth.getRefreshToken();
      if (error.status === 401 && refresh && !req.url.includes('/auth/')) {
        // Intenta refrescar el access token una vez y reintenta la request original.
        return http.post<{ access: string }>(`${environment.apiUrl}/auth/refresh/`, { refresh }).pipe(
          switchMap((res) => {
            auth.setAccessToken(res.access);
            const retryReq = req.clone({ setHeaders: { Authorization: `Bearer ${res.access}` } });
            return next(retryReq);
          }),
          catchError((refreshError) => {
            auth.logout();
            router.navigate(['/login']);
            return throwError(() => refreshError);
          })
        );
      }
      if (error.status === 401) {
        auth.logout();
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};
