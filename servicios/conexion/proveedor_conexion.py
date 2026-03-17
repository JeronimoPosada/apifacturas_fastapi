"""Lee DB_PROVIDER y las cadenas de conexión desde .env."""
# ↑ Este módulo es la implementación concreta del contrato IProveedorConexion.
# Lee la configuración centralizada (config.py) y expone:
# 1. Qué proveedor de BD está activo (postgres, mysql, etc.)
# 2. La cadena de conexión correspondiente a ese proveedor.

from config import Settings, get_settings
# ↑ Importamos de nuestro config.py:
# Settings: la clase que contiene toda la configuración.
# get_settings: función singleton que retorna el objeto Settings cacheado.


class ProveedorConexion:
    """Lee el proveedor activo y entrega la cadena de conexión."""
    # ↑ Esta clase NO hereda de IProveedorConexion.
    # Sin embargo, CUMPLE el contrato porque tiene los mismos miembros:
    # - proveedor_actual (property → str)
    # - obtener_cadena_conexion() (método → str)
    # Esto es tipado estructural (duck typing) gracias a Protocol.

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
    # ↑ Constructor de la clase.
    # settings: Settings | None = None → parámetro opcional.
    #   Si le pasan un objeto Settings, lo usa directamente.
    #   Si no le pasan nada (None), llama a get_settings() para obtener el singleton.
    # self._settings → guarda la referencia como atributo privado (convención: _prefijo).
    # El "or" funciona así: si settings es None (falsy), usa get_settings().

    @property
    def proveedor_actual(self) -> str:
        """Proveedor activo según DB_PROVIDER en .env."""
        return self._settings.database.provider.lower().strip()
    # ↑ @property → se accede como atributo: proveedor.proveedor_actual (sin paréntesis).
    # self._settings.database → accede al objeto DatabaseSettings dentro de Settings.
    # .provider → campo que lee DB_PROVIDER del .env (ej: "postgres").
    # .lower() → convierte a minúsculas ("POSTGRES" → "postgres").
    # .strip() → elimina espacios en blanco al inicio/final (" postgres " → "postgres").

    def obtener_cadena_conexion(self) -> str:
        """Cadena de conexión del proveedor activo."""
        provider = self.proveedor_actual
        # ↑ Obtiene el nombre del proveedor normalizado (ej: "postgres").

        db_config = self._settings.database
        # ↑ Atajo: en vez de escribir self._settings.database cada vez,
        # guardamos la referencia en una variable local más corta.

        cadenas = {
            "postgres": db_config.postgres,
            "postgresql": db_config.postgres,
        }
        # ↑ Diccionario que mapea nombre de proveedor → cadena de conexión.
        # "postgres" y "postgresql" son aliases: ambos apuntan a la misma cadena.
        # db_config.postgres lee el campo 'postgres' de DatabaseSettings,
        # que a su vez leyó DB_POSTGRES del .env.
        #
        # NOTA: En el proyecto completo, este diccionario también incluye
        # sqlserver, mysql, mariadb, etc. Aquí solo usamos PostgreSQL.

        if provider not in cadenas:
            raise ValueError(
                f"Proveedor '{provider}' no soportado. "
                f"Opciones: {list(cadenas.keys())}"
            )
        # ↑ Validación: si el proveedor del .env no está en el diccionario,
        # lanza un error claro indicando qué opciones son válidas.
        # f"..." es un f-string: permite insertar variables dentro del texto.

        cadena = cadenas[provider]
        # ↑ Obtiene la cadena de conexión correspondiente al proveedor.

        if not cadena:
            raise ValueError(
                f"No se encontró cadena de conexión para '{provider}'. "
                f"Verificar DB_{provider.upper()} en .env"
            )
        # ↑ Validación: si la cadena está vacía (no se configuró en .env),
        # lanza un error indicando qué variable falta.
        # provider.upper() convierte "postgres" → "POSTGRES" para mostrar
        # el nombre correcto de la variable: DB_POSTGRES.

        return cadena
        # ↑ Retorna la cadena de conexión completa.
        # Ejemplo: "postgresql+asyncpg://postgres:postgres@localhost:5432/bdfacturas_postgres_local"