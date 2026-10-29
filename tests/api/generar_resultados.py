#!/usr/bin/env python3
"""Genera `resultados.md` a partir de `resultado_newman.json` (AUT-API).

Así la tabla de resultados sale siempre de la misma corrida que el reporte HTML
y no hay que copiarla a mano.

Uso (después de correr Newman con el reporter json):

    python3 generar_resultados.py auth-rbac
    python3 generar_resultados.py catalogo-turnos --entorno "API local con Docker Compose, datos `seed_demo`, rama `develop`"
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('carpeta', help='auth-rbac o catalogo-turnos')
    ap.add_argument('--entorno', default='API local con Docker Compose, datos `seed_demo`, rama `develop`',
                    help='texto del entorno que figura en la cabecera')
    ap.add_argument('--fecha', default=datetime.now().strftime('%d/%m/%Y'), help='por defecto, hoy (DD/MM/AAAA)')
    args = ap.parse_args()

    carpeta = Path(__file__).resolve().parent / args.carpeta
    datos = json.loads((carpeta / 'resultado_newman.json').read_text(encoding='utf-8'))
    run = datos['run']
    nombre = datos['collection']['info']['name']
    titulo = re.sub(r'^Barber Life - AUT-API \d+: ', '', nombre)

    filas = []
    for i, ej in enumerate(run['executions'], start=1):
        pasa = all(not a.get('error') for a in ej.get('assertions', []))
        filas.append(f"| {i} | {ej['item']['name']} | {ej['request']['method']} | "
                     f"{ej['response']['code']} | {'PASA' if pasa else 'FALLA'} |")

    stats = run['stats']
    lineas = [
        f'# Resultados AUT-API — {titulo}',
        '',
        f"- Fecha: {args.fecha} · {args.entorno}",
        f"- Requests: {stats['requests']['total']} · Aserciones: {stats['assertions']['total']} · "
        f"Fallidas: {stats['assertions']['failed']}",
        '',
        '| # | Request | Método | HTTP | Resultado |',
        '|---|---|---|---|---|',
        *filas,
        '',
    ]
    (carpeta / 'resultados.md').write_text('\n'.join(lineas), encoding='utf-8')
    print(f'resultados.md escrito en {carpeta} ({len(filas)} requests)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
