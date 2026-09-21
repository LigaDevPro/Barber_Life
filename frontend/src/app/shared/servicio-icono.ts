/** El backend no modela una categoría/ícono por Servicio — se infiere acá
 * por palabra clave en el nombre, solo para elegir un ícono en la UI. Hoy el
 * catálogo real tiene Corte de pelo, Coloración y Barba. */
const ICONOS: { match: RegExp; path: string }[] = [
  { match: /barba/i, path: 'M4 15 14 5l4 4L8 19zM14 5l2-2 4 4-2 2' },
  {
    match: /color/i,
    path: 'M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z',
  },
];

const ICONO_DEFAULT =
  'M9 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM8.12 8.12 12 12M20 4 8.12 15.88M14.8 14.8 20 20';

export function iconoServicio(nombre: string): string {
  return ICONOS.find((i) => i.match.test(nombre))?.path ?? ICONO_DEFAULT;
}
