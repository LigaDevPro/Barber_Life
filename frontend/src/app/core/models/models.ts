export type Rol = 'cliente' | 'barbero' | 'admin';

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: Rol;
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

export interface TurnosPage {
  count: number;
  page: number;
  num_pages: number;
  results: TurnoResumen[];
}
