"""Contrato del repositorio específico para producto."""
# ↑ Docstring del módulo: este archivo define el contrato (interfaz)
# que debe cumplir cualquier repositorio que maneje la tabla producto.

from typing import Protocol, Any, Optional
# ↑ Protocol: para definir la interfaz (tipado estructural).
# Any: tipo comodín — acepta cualquier tipo de dato.
#   Lo usamos en dict[str, Any] porque las columnas pueden ser
#   str, int, Decimal, etc.
# Optional: equivale a "puede ser el tipo indicado o None".
#   Optional[str] es lo mismo que str | None.
#   Lo usamos porque el esquema es opcional (si no lo envían, usa "public").


class IRepositorioProducto(Protocol):
    """Contrato para el repositorio de producto."""
    # ↑ Cualquier clase que tenga estos 5 métodos con estas firmas
    # será reconocida como un IRepositorioProducto válido.
    # No necesita escribir "class X(IRepositorioProducto)".

    async def obtener_todos(
        self,
        esquema: Optional[str] = None,
        limite: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Obtiene todos los productos."""
        ...
    # ↑ OPERACIÓN 1: LISTAR
    # async def → es una función asíncrona (se llama con await).
    # esquema: Optional[str] = None → esquema de BD (opcional, default None → usa "public").
    # limite: Optional[int] = None → máximo de filas (opcional, default None → sin límite fijo).
    # Retorna: list[dict[str, Any]] → lista de diccionarios.
    #   Ejemplo: [{"codigo": "PR001", "nombre": "Laptop", "stock": 20, "valorunitario": 2500000.00}]

    async def obtener_por_codigo(
        self,
        codigo: str,
        esquema: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Obtiene un producto por su código."""
        ...
    # ↑ OPERACIÓN 2: BUSCAR POR CÓDIGO
    # codigo: str → valor de la PK a buscar (ej: "PR001").
    # Retorna lista porque la interfaz es genérica.
    #   Si encuentra: [{"codigo": "PR001", ...}] (1 elemento).
    #   Si no encuentra: [] (lista vacía).

    async def crear(
        self,
        datos: dict[str, Any],
        esquema: Optional[str] = None
    ) -> bool:
        """Crea un nuevo producto. Retorna True si se creó."""
        ...
    # ↑ OPERACIÓN 3: CREAR (INSERT)
    # datos: dict[str, Any] → diccionario con los campos del producto.
    #   Ejemplo: {"codigo": "PR006", "nombre": "Mouse", "stock": 10, "valorunitario": 50000}
    # Retorna: bool → True si el INSERT afectó al menos 1 fila, False si no.

    async def actualizar(
        self,
        codigo: str,
        datos: dict[str, Any],
        esquema: Optional[str] = None
    ) -> int:
        """Actualiza un producto. Retorna filas afectadas."""
        ...
    # ↑ OPERACIÓN 4: ACTUALIZAR (UPDATE)
    # codigo: str → PK del producto a actualizar.
    # datos: dict[str, Any] → campos a modificar (sin incluir el código).
    #   Ejemplo: {"nombre": "Mouse Gamer", "stock": 15}
    # Retorna: int → número de filas afectadas (0 si no encontró el producto).

    async def eliminar(
        self,
        codigo: str,
        esquema: Optional[str] = None
    ) -> int:
        """Elimina un producto. Retorna filas eliminadas."""
        ...
    # ↑ OPERACIÓN 5: ELIMINAR (DELETE)
    # codigo: str → PK del producto a eliminar.
    # Retorna: int → número de filas eliminadas (0 si no existía).