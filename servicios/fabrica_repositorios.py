"""
fabrica_repositorios.py — Factory centralizada.

Lee DB_PROVIDER del .env y crea el repositorio y servicio correspondientes.
"""
# ↑ Docstring del módulo. Este archivo implementa el patrón FACTORY:
# una función que CREA objetos sin que el código cliente (controller)
# necesite conocer las clases concretas.

from servicios.conexion.proveedor_conexion import ProveedorConexion
# ↑ Importa la clase que lee la configuración de conexión del .env.

from repositorios.producto import RepositorioProductoPostgreSQL
# ↑ Importa el repositorio concreto de producto para PostgreSQL.
# Si en el futuro agregas MySQL, aquí importarías también
# RepositorioProductoMysqlMariaDB.

from servicios.servicio_producto import ServicioProducto
# ↑ Importa el servicio de producto (lógica de negocio).


# =====================================================================
# HELPERS INTERNOS
# =====================================================================

def _obtener_proveedor():
    """Obtiene el proveedor de conexión y su nombre."""
    proveedor = ProveedorConexion()
    return proveedor, proveedor.proveedor_actual
# ↑ Función auxiliar (privada por convención: empieza con _).
# 1. Crea un ProveedorConexion (lee .env vía config.py)
# 2. Retorna una tupla: (objeto_proveedor, "postgres")
# Se usa en todas las fábricas para no repetir este código.


def _crear_repo_entidad(repos_por_proveedor: dict, proveedor, nombre: str):
    """Instancia el repositorio específico según el proveedor activo."""
    clase = repos_por_proveedor.get(nombre)
    if clase is None:
        raise ValueError(
            f"Proveedor '{nombre}' no soportado para esta entidad. "
            f"Opciones: {list(repos_por_proveedor.keys())}"
        )
    return clase(proveedor)
# ↑ Función auxiliar genérica que crea un repositorio.
# repos_por_proveedor: diccionario {"postgres": ClaseRepo, "mysql": ClaseRepo, ...}
# proveedor: objeto ProveedorConexion
# nombre: string del proveedor activo (ej: "postgres")
#
# Flujo:
# 1. Busca la clase en el diccionario: repos_por_proveedor["postgres"]
#    → RepositorioProductoPostgreSQL
# 2. Si no existe, lanza error con las opciones válidas
# 3. Crea una instancia: RepositorioProductoPostgreSQL(proveedor)
#    → Le pasa el proveedor de conexión al constructor


# =====================================================================
# FACTORY DE PRODUCTO
# =====================================================================

_REPOS_PRODUCTO = {
    "postgres": RepositorioProductoPostgreSQL,
    "postgresql": RepositorioProductoPostgreSQL,
}
# ↑ Diccionario que mapea nombre de proveedor → clase de repositorio.
# "postgres" y "postgresql" son aliases: ambos apuntan a la misma clase.
#
# Para agregar soporte MySQL en el futuro, solo agregas:
#   "mysql": RepositorioProductoMysqlMariaDB,
#   "mariadb": RepositorioProductoMysqlMariaDB,
# ¡Sin tocar NADA más! Esto es el principio Open/Closed de SOLID.
#
# NOTA: En el proyecto completo (ApiFacturasFastApi_Crud), este diccionario
# también incluye sqlserver, sqlserverexpress, localdb, mysql, mariadb.


def crear_servicio_producto() -> ServicioProducto:
    """Crea el servicio específico de producto."""
    proveedor, nombre = _obtener_proveedor()
    repo = _crear_repo_entidad(_REPOS_PRODUCTO, proveedor, nombre)
    return ServicioProducto(repo)
# ↑ LA FUNCIÓN QUE USA EL CONTROLLER.
# Es la ÚNICA función pública de este archivo para producto.
#
# Flujo completo:
# 1. _obtener_proveedor()
#    → ProveedorConexion() lee .env → DB_PROVIDER = "postgres"
#    → Retorna: (proveedor_obj, "postgres")
#
# 2. _crear_repo_entidad(_REPOS_PRODUCTO, proveedor_obj, "postgres")
#    → Busca en el diccionario: _REPOS_PRODUCTO["postgres"]
#    → Obtiene: RepositorioProductoPostgreSQL
#    → Crea: RepositorioProductoPostgreSQL(proveedor_obj)
#    → Retorna: instancia del repositorio
#
# 3. ServicioProducto(repo)
#    → Crea el servicio inyectándole el repositorio
#    → El servicio no sabe si el repo es PostgreSQL, MySQL o un mock
#
# 4. Retorna el servicio listo para usar.
#
# El controller solo hace:
#   servicio = crear_servicio_producto()
#   datos = await servicio.listar()