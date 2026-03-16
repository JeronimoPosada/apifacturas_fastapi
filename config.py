"""
config.py — Configuración centralizada usando pydantic-settings.

Lee variables desde archivos .env según el entorno:
- Production:  solo .env
- Development: .env + .env.development (sobrescribe valores)

Este archivo implementa el patrón SINGLETON con @lru_cache:
la configuración se lee del disco una sola vez y se reutiliza
en todas las llamadas posteriores.
"""

# ─── Imports ─────────────────────────────────────────────────

import os                       # Módulo estándar de Python para interactuar con el sistema operativo.
                                # Lo usamos para leer la variable de entorno ENVIRONMENT y
                                # verificar si existe el archivo .env.development.

from functools import lru_cache # lru_cache es un decorador que CACHEA el resultado de una función.
                                # La primera vez que llamas a la función, ejecuta el código y guarda
                                # el resultado. Las siguientes veces, retorna el resultado guardado
                                # sin ejecutar el código de nuevo. Esto implementa el patrón SINGLETON.

from pydantic import Field      # Field permite definir valores por defecto, aliases y validaciones
                                # para los campos de las clases Settings.

from pydantic_settings import BaseSettings, SettingsConfigDict
                                # BaseSettings: clase base que lee automáticamente variables de entorno.
                                # SettingsConfigDict: configuración de cómo leer los archivos .env
                                # (nombre del archivo, encoding, prefijo de variables, etc.).


# ═════════════════════════════════════════════════════════════
# DETECCIÓN DE ENTORNO
# ═════════════════════════════════════════════════════════════

def get_environment() -> str:
    """
    Detecta el entorno actual desde la variable ENVIRONMENT.

    Si ENVIRONMENT no está definida en el sistema, usa "production"
    como valor por defecto (lo más seguro para producción).
    .lower() convierte a minúsculas para evitar errores por mayúsculas.
    """
    return os.getenv("ENVIRONMENT", "production").lower()
    # os.getenv("ENVIRONMENT", "production")
    #   → Busca la variable ENVIRONMENT en el sistema operativo.
    #   → Si no existe, retorna "production" (valor por defecto seguro).
    # .lower()
    #   → Convierte a minúsculas: "Development" → "development".


def get_env_file() -> str | tuple[str, str]:
    """
    Retorna qué archivo(s) .env cargar según el entorno.

    En development: carga .env y luego .env.development.
    Los valores de .env.development sobrescriben los de .env.
    Esto permite tener configuraciones diferentes por entorno.

    En production: solo carga .env.
    """
    env = get_environment()             # Lee el entorno actual ("development" o "production")
    if env == "development":            # Si estamos en desarrollo...
        env_dev = ".env.development"    # Nombre del archivo de desarrollo
        if os.path.exists(env_dev):     # Solo si el archivo existe en disco
            return (".env", env_dev)    # Retorna AMBOS archivos como tupla
    return ".env"                       # En producción (o si no existe .env.development)


# ═════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE BASE DE DATOS
# ═════════════════════════════════════════════════════════════

class DatabaseSettings(BaseSettings):
    """
    Cadenas de conexión para cada proveedor de base de datos.

    BaseSettings lee automáticamente las variables de entorno que
    coincidan con los nombres de los campos (con el prefijo DB_).

    Ejemplo: el campo 'postgres' lee la variable DB_POSTGRES del .env.
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file(),        # Qué archivo(s) .env leer
        env_file_encoding='utf-8',      # Encoding del archivo (soporta caracteres especiales)
        env_prefix='DB_',               # PREFIJO: solo lee variables que empiezan con DB_
                                        # Así, DB_PROVIDER se mapea al campo "provider",
                                        # DB_POSTGRES se mapea al campo "postgres", etc.
        extra='ignore'                  # Ignorar variables extra que no coincidan con campos
    )

    # Proveedor activo — determina qué repositorio y cadena de conexión usar.
    # Lee DB_PROVIDER del .env. Si no existe, usa "postgres" por defecto.
    provider: str = Field(default='postgres')

    # Cadenas de conexión por proveedor.
    # Cada campo lee su variable DB_ correspondiente del .env.
    # Si la variable no existe, usa string vacío como valor por defecto.
    postgres: str = Field(default='')       # Lee DB_POSTGRES


# ═════════════════════════════════════════════════════════════
# CONFIGURACIÓN PRINCIPAL
# ═════════════════════════════════════════════════════════════

class Settings(BaseSettings):
    """
    Agrupa toda la configuración de la aplicación.

    Esta clase es el punto de entrada para acceder a cualquier
    configuración. Contiene configuraciones generales (debug, environment)
    y una instancia de DatabaseSettings para las cadenas de conexión.
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file(),        # Mismos archivos .env que DatabaseSettings
        env_file_encoding='utf-8',      # Mismo encoding
        extra='ignore'                  # Ignorar variables extra
    )

    # Campo debug: lee la variable DEBUG del .env.
    # alias='DEBUG' permite que el campo en Python sea minúscula (debug)
    # pero lea la variable en mayúscula (DEBUG) del .env.
    debug: bool = Field(default=False, alias='DEBUG')

    # Campo environment: usa la función get_environment() como valor por defecto.
    # default_factory significa: "llama a esta función para obtener el valor".
    environment: str = Field(default_factory=get_environment)

    # Campo database: crea una instancia de DatabaseSettings.
    # default_factory=DatabaseSettings significa: "crea un DatabaseSettings nuevo".
    # Esto lee automáticamente todas las variables DB_* del .env.
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


# ═════════════════════════════════════════════════════════════
# SINGLETON (se crea una sola vez y se reutiliza)
# ═════════════════════════════════════════════════════════════

@lru_cache()    # ← PATRÓN SINGLETON.
                # La primera vez que alguien llama a get_settings():
                #   1. Crea un objeto Settings() (lee el .env del disco)
                #   2. Lo guarda en memoria (cache)
                #   3. Lo retorna
                # Las siguientes veces:
                #   1. Retorna el objeto guardado SIN leer el disco de nuevo
                # Resultado: el .env se lee UNA SOLA VEZ en toda la vida de la app.
def get_settings() -> Settings:
    """Obtiene la configuración cacheada (singleton)."""
    return Settings()