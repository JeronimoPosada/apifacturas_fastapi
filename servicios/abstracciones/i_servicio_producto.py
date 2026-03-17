"""Contrato del servicio específico para producto."""
# ↑ Docstring del módulo: define el contrato que debe cumplir
# cualquier implementación del servicio de producto.

from typing import Protocol, Any, Optional
# ↑ Protocol: para definir la interfaz (tipado estructural).
# Any: tipo comodín (las columnas pueden ser str, int, Decimal, etc.).
# Optional: equivale a "el tipo indicado o None".


class IServicioProducto(Protocol):
    """Contrato del servicio específico para producto."""
    # ↑ Interfaz del servicio. Cualquier clase que tenga estos 5 métodos
    # con estas firmas será reconocida como un IServicioProducto válido.
    #
    # Nota: los nombres de los métodos son de NEGOCIO, no de SQL:
    #   "listar" (no "select_all")
    #   "crear" (no "insert")
    #   "actualizar" (no "update")
    #   "eliminar" (no "delete")

    async def listar(
        self, esquema: Optional[str] = None,
        limite: Optional[int] = None
    ) -> list[dict[str, Any]]:
        ...
    # ↑ OPERACIÓN 1: LISTAR todos los productos.
    # esquema: esquema de BD (opcional, default "public").
    # limite: máximo de resultados (opcional).
    # Retorna: lista de diccionarios con los datos de cada producto.

    async def obtener_por_codigo(
        self, codigo: str,
        esquema: Optional[str] = None
    ) -> list[dict[str, Any]]:
        ...
    # ↑ OPERACIÓN 2: BUSCAR un producto por su código.
    # codigo: PK del producto (ej: "PR001").
    # Retorna: lista con 0 o 1 elemento.

    async def crear(
        self, datos: dict[str, Any],
        esquema: Optional[str] = None
    ) -> bool:
        ...
    # ↑ OPERACIÓN 3: CREAR un producto nuevo.
    # datos: diccionario con los campos (codigo, nombre, stock, valorunitario).
    # Retorna: True si se creó exitosamente.

    async def actualizar(
        self, codigo: str,
        datos: dict[str, Any],
        esquema: Optional[str] = None
    ) -> int:
        ...
    # ↑ OPERACIÓN 4: ACTUALIZAR un producto existente.
    # codigo: PK del producto a actualizar.
    # datos: campos a modificar (sin incluir el código).
    # Retorna: número de filas afectadas (0 si no encontró el producto).

    async def eliminar(
        self, codigo: str,
        esquema: Optional[str] = None
    ) -> int:
        ...
    # ↑ OPERACIÓN 5: ELIMINAR un producto.
    # codigo: PK del producto a eliminar.
    # Retorna: número de filas eliminadas (0 si no existía).