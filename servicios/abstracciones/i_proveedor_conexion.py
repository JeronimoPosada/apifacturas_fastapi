"""Contrato para obtener información de conexión a BD."""
# ↑ Docstring del módulo: describe el propósito del archivo.
# Python lo usa como documentación cuando haces help() sobre el módulo.

from typing import Protocol
# ↑ Importamos Protocol del módulo typing (tipos de Python).
# Protocol es la clase base para definir interfaces estructurales.
# Una clase que tenga los mismos métodos que este Protocol
# será reconocida automáticamente como implementación válida,
# sin necesidad de heredar explícitamente.


class IProveedorConexion(Protocol):
    """Contrato para clases que proveen información de conexión."""
    # ↑ La "I" al inicio es convención: indica que es una Interface.
    # Heredar de Protocol convierte esta clase en una interfaz estructural.
    # NINGUNA clase necesita escribir "class X(IProveedorConexion)" para cumplir.
    # Solo necesita tener los mismos métodos con las mismas firmas.

    @property
    def proveedor_actual(self) -> str:
        """Nombre del proveedor activo (ej: 'postgres')."""
        ...
    # ↑ @property define un método que se accede como atributo:
    #   proveedor.proveedor_actual  (sin paréntesis, como un campo)
    # → str: debe retornar un string con el nombre del proveedor.
    # Los "..." (Ellipsis) significan "sin implementación" — es solo la firma.

    def obtener_cadena_conexion(self) -> str:
        """Cadena de conexión del proveedor activo."""
        ...
    # ↑ Método que retorna la cadena de conexión completa.
    # Ejemplo: "postgresql+asyncpg://postgres:postgres@localhost:5432/bdfacturas"
    # Los "..." indican que este método no tiene cuerpo aquí.
    # La clase que implemente este contrato definirá el cuerpo.