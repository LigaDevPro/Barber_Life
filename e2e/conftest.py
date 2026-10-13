"""Fixtures compartidas de la suite E2E (AUT-E2E).

Variables de entorno (todas con valor por defecto para el entorno local de
docker compose):

    BASE_URL        SPA Angular            (http://localhost:4200)
    API_URL         API Django REST        (http://localhost:8000/api)
    ADMIN_EMAIL     / ADMIN_PASSWORD       (cuentas de `manage.py seed_demo`)
"""
import json
import os
import urllib.request
import uuid

import pytest

API_URL = os.environ.get('API_URL', 'http://localhost:8000/api').rstrip('/')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@barberlife.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')
PASSWORD_CLIENTE = 'Cliente-E2E-2026'


@pytest.fixture(scope='session')
def base_url():
    return os.environ.get('BASE_URL', 'http://localhost:4200').rstrip('/')


@pytest.fixture(scope='session')
def credenciales_admin():
    return {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD}


@pytest.fixture
def cliente_nuevo():
    """Crea un cliente único por test vía API (no depende de datos previos ni
    de la UI de registro) y devuelve sus credenciales."""
    email = f'e2e.{uuid.uuid4().hex[:10]}@mail.com'
    payload = json.dumps({
        'email': email,
        'password': PASSWORD_CLIENTE,
        'password_confirm': PASSWORD_CLIENTE,
    }).encode()
    req = urllib.request.Request(
        f'{API_URL}/auth/register/', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 201, f'No se pudo crear el cliente de prueba ({resp.status})'
    return {'email': email, 'password': PASSWORD_CLIENTE}
