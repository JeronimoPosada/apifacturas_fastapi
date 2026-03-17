"""Repositorio de producto para PostgreSQL."""
# ↑ Docstring del módulo: este archivo contiene la implementación
# concreta del repositorio de producto para PostgreSQL.

from repositorios.base_repositorio_postgresql import BaseRepositorioPostgreSQL
# ↑ Importamos la clase base que tiene toda la lógica SQL.
# Esta clase hereda de ella para reutilizar los 5 métodos protegidos:
# _obtener_filas, _obtener_por_clave, _crear, _actualizar, _eliminar.


class RepositorioProductoPostgreSQL(BaseRepositorioPostgreSQL):
    """Acceso a datos de producto en PostgreSQL."""
    # ↑ Hereda de BaseRepositorioPostgreSQL.
    # Esto le da acceso a TODOS los métodos de la clase base.
    # Esta clase no necesita el constructor (__init__) porque
    # usa el del padre (que recibe proveedor_conexion).

    TABLA = "producto"
    # ↑ Constante de clase: nombre de la tabla en la BD.
    # Se pasa como parámetro a los métodos de la clase base.

    CLAVE_PRIMARIA = "codigo"
    # ↑ Constante de clase: nombre de la columna PK.
    # Se pasa como parámetro a _obtener_por_clave, _actualizar, _eliminar.

    async def obtener_todos(self, esquema=None, limite=None):
        """Obtiene todos los productos."""
        return await self._obtener_filas(self.TABLA, esquema, limite)
    # ↑ OPERACIÓN 1: LISTAR
    # Delega completamente a la clase base.
    # self.TABLA → "producto"
    # Resultado: SELECT * FROM "public"."producto" LIMIT 1000

    async def obtener_por_codigo(self, codigo, esquema=None):
        """Obtiene un producto por su codigo."""
        return await self._obtener_por_clave(
            self.TABLA, self.CLAVE_PRIMARIA, str(codigo), esquema
        )
    # ↑ OPERACIÓN 2: BUSCAR POR CÓDIGO
    # self.TABLA → "producto", self.CLAVE_PRIMARIA → "codigo"
    # str(codigo) → convierte a string por seguridad.
    # Resultado: SELECT * FROM "public"."producto" WHERE "codigo" = :valor

    async def crear(self, datos, esquema=None):
        """Crea un nuevo producto."""
        return await self._crear(self.TABLA, datos, esquema)
    # ↑ OPERACIÓN 3: CREAR
    # datos es un dict: {"codigo": "PR006", "nombre": "Mouse", "stock": 10, ...}
    # Resultado: INSERT INTO "public"."producto" ("codigo", ...) VALUES (:codigo, ...)

    async def actualizar(self, codigo, datos, esquema=None):
        """Actualiza un producto existente."""
        return await self._actualizar(
            self.TABLA, self.CLAVE_PRIMARIA, str(codigo), datos, esquema
        )
    # ↑ OPERACIÓN 4: ACTUALIZAR
    # Resultado: UPDATE "public"."producto" SET ... WHERE "codigo" = :valor_clave

    async def eliminar(self, codigo, esquema=None):
        """Elimina un producto por su codigo."""
        return await self._eliminar(
            self.TABLA, self.CLAVE_PRIMARIA, str(codigo), esquema
        )
    # ↑ OPERACIÓN 5: ELIMINAR
    # Resultado: DELETE FROM "public"."producto" WHERE "codigo" = :valor_clave