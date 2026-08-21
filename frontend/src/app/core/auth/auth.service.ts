import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginResponse, Usuario } from '../models/models';

const ACCESS_KEY = 'bl_access_token';
const REFRESH_KEY = 'bl_refresh_token';
const USER_KEY = 'bl_usuario';

@Injectable({ providedIn: 'root' })
export class AuthService {
  /** Estado reactivo del usuario logueado; null si no hay sesión. */
  currentUser = signal<Usuario | null>(this.readStoredUser());

  constructor(private http: HttpClient) {}

  private readStoredUser(): Usuario | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as Usuario) : null;
  }

  register(email: string, password: string, passwordConfirm: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${environment.apiUrl}/auth/register/`, {
      email,
      password,
      password_confirm: passwordConfirm,
    });
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login/`, { email, password }).pipe(
      tap((res) => {
        localStorage.setItem(ACCESS_KEY, res.access);
        localStorage.setItem(REFRESH_KEY, res.refresh);
        localStorage.setItem(USER_KEY, JSON.stringify(res.usuario));
        this.currentUser.set(res.usuario);
      })
    );
  }

  refreshMe(): Observable<Usuario> {
    return this.http.get<Usuario>(`${environment.apiUrl}/auth/me/`).pipe(
      tap((usuario) => {
        localStorage.setItem(USER_KEY, JSON.stringify(usuario));
        this.currentUser.set(usuario);
      })
    );
  }

  logout(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  setAccessToken(token: string): void {
    localStorage.setItem(ACCESS_KEY, token);
  }

  isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }
}
