export type Rol = 'cliente' | 'barbero' | 'admin';
export type EstadoUsuario = 'activo' | 'inactivo';

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: Rol;
  estado: EstadoUsuario;
  telefono: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  usuario: Usuario;
}

export interface TurnoPorDia {
  dia: string;
  cantidad: number;
}

export interface TurnoResumen {
  id: number;
  cliente_nombre: string;
  servicio_nombre: string;
  hora: string;
  fecha: string;
  estado: 'pendiente' | 'confirmado' | 'completado' | 'cancelado';
  precio_total: string;
  observaciones: string;
  puede_cancelar: boolean;
}

export interface DashboardData {
  rol: Rol;
  nombre: string;
  turnos_hoy: number;
  clientes_activos: number;
  ingresos_del_mes: string | null;
  turnos_por_semana: TurnoPorDia[];
  ultimos_turnos: TurnoResumen[];
}

export interface ServicioMasSolicitado {
  servicio_id: number;
  nombre: string;
  precio: string;
  cantidad: number;
}

/** Shape de paginación compartido por todos los listados paginados del
 * backend (Turnos y Notificaciones hoy; ver `PaginacionEstandar` y el
 * paginado manual con skip/limit de `NotificacionListView`). */
export interface Pagina<T> {
  count: number;
  page: number;
  num_pages: number;
  results: T[];
}

export type TurnosPage = Pagina<TurnoResumen>;

// ---------------------------------------------------------------------------
// Paquete 1 — Perfiles: Cliente + Barbero
// ---------------------------------------------------------------------------

export interface Cliente {
  id: number;
  fecha_nacimiento: string | null;
  fecha_registro: string;
  activo: boolean;
  telefono: string;
  usuario: Usuario;
}

export interface HorarioInline {
  id: number;
  dia_semana: number;
  dia_semana_display: string;
  hora_inicio: string;
  hora_fin: string;
  intervalo_minutos: number;
}

export interface ServicioOfrecidoInline {
  id: number;
  servicio: number;
  servicio_nombre: string;
  precio: string;
  horario: number;
}

export interface BarberoPublic {
  id: number;
  nombre: string;
  foto_perfil_url: string;
  activo: boolean;
}

export interface BarberoDetail extends BarberoPublic {
  horarios: HorarioInline[];
  servicios_ofrecidos: ServicioOfrecidoInline[];
}

export interface BarberoMe {
  id: number;
  foto_perfil_url: string;
  activo: boolean;
  fecha_creacion: string;
  usuario: Usuario;
}

// ---------------------------------------------------------------------------
// Paquete 3 — Catálogo y disponibilidad: Servicio, Horario, BarberoServicio
// ---------------------------------------------------------------------------

export interface Servicio {
  id: number;
  nombre: string;
  duracion_minutos: number;
  precio: string;
  activo: boolean;
}

export interface Horario {
  id: number;
  barbero: number;
  dia_semana: number;
  dia_semana_display: string;
  hora_inicio: string;
  hora_fin: string;
  intervalo_minutos: number;
  activo: boolean;
}

export interface BarberoServicio {
  id: number;
  barbero: number;
  servicio: number;
  servicio_nombre: string;
  horario: number;
  precio_personalizado: string | null;
  precio: string;
  activo: boolean;
  fecha_creacion: string;
}

// ---------------------------------------------------------------------------
// Paquete 4 — Pagos (Mercado Pago)
// ---------------------------------------------------------------------------

export type MetodoPago = 'mercado_pago' | 'efectivo';
export type EstadoPago = 'pendiente' | 'aprobado' | 'rechazado' | 'reembolsado';

export interface Pago {
  id: number;
  turno: number;
  monto_total: string;
  metodo_pago: MetodoPago;
  estado: EstadoPago;
  fecha_pago: string | null;
  transaccion_id: string | null;
  fecha_creacion: string;
}

/** Respuesta de POST /api/pagos/ — no es el `Pago` completo, la arma la
 * vista a mano con lo que hace falta para redirigir a Mercado Pago. */
export interface PagoCreateResponse {
  id: number;
  init_point: string;
  estado: EstadoPago;
}

// ---------------------------------------------------------------------------
// Paquete 5 — Notificaciones (Mongo)
// ---------------------------------------------------------------------------

export interface Notificacion {
  id: string;
  tipo: string;
  mensaje: string;
  canal: string;
  leida: boolean;
  fecha_creacion: string;
}
