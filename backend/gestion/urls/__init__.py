"""
Junta las urlpatterns de cada dominio en una sola lista, que es lo que
`core/urls.py` incluye con `include('gestion.urls')`. Cada dominio agrega su
propio archivo acá (auth, dashboard, turno, cliente, barbero, ...) para que
distintas personas puedan sumar sus endpoints sin pisarse en el mismo
archivo.
"""
from . import auth, dashboard, turno, cliente, barbero

urlpatterns = (
    auth.urlpatterns
    + dashboard.urlpatterns
    + turno.urlpatterns
    + cliente.urlpatterns
    + barbero.urlpatterns
)
