from rest_framework.exceptions import NotFound


class PerfilPropioMixin:
    """Para vistas RetrieveUpdateAPIView de 'perfil propio' (Cliente, Barbero):
    resuelve el objeto desde request.user.<perfil_attr> en vez del pk de la
    URL, y devuelve 404 con mensaje claro si el usuario no tiene ese perfil."""
    perfil_attr = None
    perfil_no_encontrado_mensaje = 'Tu usuario no tiene el perfil asociado.'

    def get_object(self):
        perfil = getattr(self.request.user, self.perfil_attr, None)
        if perfil is None:
            raise NotFound(self.perfil_no_encontrado_mensaje)
        return perfil
