FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Junta los estáticos (admin, DRF) en STATIC_ROOT para que los sirva whitenoise.
# La clave es solo para que settings.py cargue durante el build; no se usa en runtime.
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

EXPOSE 8000

# Producción: daphne (ASGI, atiende HTTP y WebSockets) en el puerto que asigne la
# plataforma ($PORT; 8000 si no existe). Aplica las migraciones antes de arrancar.
# docker-compose.yml pisa este comando con runserver para desarrollo.
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne -b 0.0.0.0 -p ${PORT:-8000} core.asgi:application"]
