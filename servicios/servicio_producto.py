"""Servicio específico para la entidad producto."""
# ↑ Docstring del módulo. Este archivo implementa la lógica de negocio
# para la entidad producto: validaciones, normalización de parámetros
# y delegación al repositorio.

from typing import Any
# ↑ Any: tipo comodín. Lo usamos en dict[str, Any] porque los valores
# de las columnas pueden ser de distintos tipos (str, int, Decimal).


class ServicioProducto:
    """Lógica de negocio para producto."""
    # ↑ Esta clase NO hereda de IServicioProducto.
    # Cumple el contrato por tipado estructural (duck typing):
    # tiene los 5 métodos con las firmas correctas → es válido.

    def __init__(self, repositorio):
        if repositorio is None:
            raise ValueError("repositorio no puede ser None.")
        self._repo = repositorio
    # ↑ Constructor.
    # repositorio → recibe el repositorio de producto (cualquier implementación).
    #   No especifica el tipo concreto (RepositorioProductoPostgreSQL).
    #   Podría ser PostgreSQL, MySQL, o un mock para pruebas.
    #   Esto es INVERSIÓN DE DEPENDENCIAS: depende de la abstracción.
    # Validación: si es None, lanza error inmediato (fail fast).
    # self._repo → guarda la referencia como atributo privado.

    async def listar(self, esquema: str | None = None, limite: int | None = None) -> list[dict[str, Any]]:
        esquema_norm = esquema.strip() if esquema and esquema.strip() else None
        limite_norm = limite if limite and limite > 0 else None
        return await self._repo.obtener_todos(esquema_norm, limite_norm)
    # ↑ OPERACIÓN 1: LISTAR
    #
    # NORMALIZACIÓN DE PARÁMETROS:
    # esquema_norm:
    #   esquema = "  public  " → "public" (strip quita espacios)
    #   esquema = "  " → None (string vacío o solo espacios → None)
    #   esquema = None → None (se queda None)
    #   La condición "esquema and esquema.strip()" verifica:
    #     1. que esquema no sea None (primer "esquema")
    #     2. que después de strip no quede vacío (esquema.strip())
    #
    # limite_norm:
    #   limite = 50 → 50 (número positivo, se mantiene)
    #   limite = 0 → None (cero no es un límite útil)
    #   limite = -5 → None (negativo no tiene sentido)
    #   limite = None → None (se queda None)
    #
    # Luego DELEGA al repositorio: self._repo.obtener_todos()
    # El servicio NO ejecuta SQL — solo valida y delega.

    async def obtener_por_codigo(self, codigo: str, esquema: str | None = None) -> list[dict[str, Any]]:
        if not codigo or not codigo.strip():
            raise ValueError("El código no puede estar vacío.")
        esquema_norm = esquema.strip() if esquema and esquema.strip() else None
        return await self._repo.obtener_por_codigo(codigo, esquema_norm)
    # ↑ OPERACIÓN 2: BUSCAR POR CÓDIGO
    #
    # VALIDACIÓN DE NEGOCIO:
    #   "not codigo" → True si codigo es None o ""
    #   "not codigo.strip()" → True si codigo es "   " (solo espacios)
    #   Si el código es inválido, lanza ValueError ANTES de llamar al repo.
    #   Esto evita que el repositorio reciba datos basura.
    #
    # NORMALIZACIÓN: esquema se normaliza igual que en listar().
    # DELEGACIÓN: self._repo.obtener_por_codigo(codigo, esquema_norm)

    async def crear(self, datos: dict[str, Any], esquema: str | None = None) -> bool:
        if not datos:
            raise ValueError("Los datos no pueden estar vacíos.")
        esquema_norm = esquema.strip() if esquema and esquema.strip() else None
        return await self._repo.crear(datos, esquema_norm)
    # ↑ OPERACIÓN 3: CREAR
    #
    # VALIDACIÓN: "not datos" es True si datos es None, {} o está vacío.
    #   No tiene sentido hacer un INSERT sin datos.
    #
    # Nota: la validación de TIPOS (que stock sea int, que valorunitario
    # sea decimal) la hace Pydantic en el controller (Parte 5).
    # El servicio solo valida que los datos no estén vacíos.

    async def actualizar(self, codigo: str, datos: dict[str, Any], esquema: str | None = None) -> int:
        if not codigo or not codigo.strip():
            raise ValueError("El código no puede estar vacío.")
        if not datos:
            raise ValueError("Los datos no pueden estar vacíos.")
        esquema_norm = esquema.strip() if esquema and esquema.strip() else None
        return await self._repo.actualizar(codigo, datos, esquema_norm)
    # ↑ OPERACIÓN 4: ACTUALIZAR
    #
    # VALIDACIONES:
    #   1. El código no puede ser vacío (¿qué producto actualizar?)
    #   2. Los datos no pueden ser vacíos (¿qué cambiar?)
    # Ambas validaciones protegen al repositorio de operaciones sin sentido.

    async def eliminar(self, codigo: str, esquema: str | None = None) -> int:
        if not codigo or not codigo.strip():
            raise ValueError("El código no puede estar vacío.")
        esquema_norm = esquema.strip() if esquema and esquema.strip() else None
        return await self._repo.eliminar(codigo, esquema_norm)
    # ↑ OPERACIÓN 5: ELIMINAR
    #
    # VALIDACIÓN: el código no puede ser vacío.
    # DELEGACIÓN: self._repo.eliminar(codigo, esquema_norm)