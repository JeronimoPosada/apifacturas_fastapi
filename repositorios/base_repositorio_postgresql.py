"""
base_repositorio_postgresql.py — Clase base con lógica SQL para PostgreSQL.

Características de PostgreSQL:
- Identificadores con "comillas dobles"
- LIMIT n para limitar resultados
- Esquema por defecto: 'public'
"""
# ↑ Docstring del módulo. Documenta las particularidades de PostgreSQL
# que se reflejan en el SQL generado por esta clase.
# - "comillas dobles": PostgreSQL usa "tabla" en vez de [tabla] (SQL Server)
#   o `tabla` (MySQL). Esto permite nombres con mayúsculas o espacios.
# - LIMIT n: PostgreSQL usa LIMIT (MySQL también), mientras que
#   SQL Server usa TOP n.
# - Esquema 'public': PostgreSQL organiza tablas en esquemas.
#   El esquema por defecto es 'public'.

from typing import Any
# ↑ Any: tipo comodín de Python. Acepta cualquier tipo.
# Lo usamos en dict[str, Any] porque las columnas de la BD pueden
# ser string, entero, decimal, fecha, booleano, etc.

from datetime import datetime, date, time
# ↑ Tipos de fecha/hora de Python.
# datetime: fecha + hora (2024-01-15 14:30:00)
# date: solo fecha (2024-01-15)
# time: solo hora (14:30:00)
# Los necesitamos para convertir valores que vienen de la BD.

from decimal import Decimal
# ↑ Tipo Decimal de Python: números con precisión exacta.
# Los campos NUMERIC(14,2) de PostgreSQL llegan como Decimal en Python.
# Ejemplo: Decimal('2500000.00') en vez de float 2500000.0
# Decimal es más preciso que float para valores monetarios.

from uuid import UUID
# ↑ Tipo UUID (Universally Unique Identifier).
# Es un identificador de 128 bits: "550e8400-e29b-41d4-a716-446655440000"
# Algunas tablas usan UUID como PK en vez de SERIAL o VARCHAR.

from sqlalchemy import text
# ↑ Función text() de SQLAlchemy.
# Permite escribir SQL crudo con parámetros seguros.
# text("SELECT * FROM producto WHERE codigo = :codigo")
# Los :parametros se reemplazan de forma segura (previene SQL injection).

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
# ↑ Componentes async de SQLAlchemy:
# create_async_engine: crea un pool de conexiones asíncronas.
#   Es la "puerta de entrada" a la base de datos.
# AsyncEngine: tipo del objeto engine (para type hints).

from servicios.abstracciones.i_proveedor_conexion import IProveedorConexion
# ↑ Importamos el contrato (interfaz) del proveedor de conexión.
# Esta clase base DEPENDE de la abstracción (IProveedorConexion),
# no de la implementación concreta (ProveedorConexion).
# Esto cumple el principio D de SOLID (Inversión de Dependencias).


class BaseRepositorioPostgreSQL:
    """Clase base con la lógica SQL de PostgreSQL. Los repositorios específicos heredan de esta clase."""
    # ↑ Esta clase es ABSTRACTA en el sentido de que no se usa directamente.
    # Siempre se usa a través de una subclase como RepositorioProductoPostgreSQL.
    # Los métodos empiezan con _ (protegidos): solo las subclases los llaman.

    def __init__(self, proveedor_conexion: IProveedorConexion):
        if proveedor_conexion is None:
            raise ValueError("proveedor_conexion no puede ser None")
        self._proveedor_conexion = proveedor_conexion
        self._engine: AsyncEngine | None = None
    # ↑ Constructor.
    # proveedor_conexion: IProveedorConexion → recibe el proveedor de conexión.
    #   El tipo es la INTERFAZ (Protocol), no la clase concreta.
    #   Esto es Inversión de Dependencias: depende de la abstracción.
    # Validación: si es None, lanza error inmediato (fail fast).
    # self._proveedor_conexion → guarda la referencia (atributo privado).
    # self._engine → el motor de conexión (se crea la primera vez que se necesita).
    #   Empieza como None y se inicializa en _obtener_engine() (lazy loading).

    async def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine de conexión la primera vez, luego lo reutiliza."""
        if self._engine is None:
            cadena = self._proveedor_conexion.obtener_cadena_conexion()
            self._engine = create_async_engine(cadena, echo=False)
        return self._engine
    # ↑ Método asíncrono que retorna el engine de SQLAlchemy.
    # PATRÓN LAZY LOADING: no crea el engine hasta que realmente se necesita.
    # if self._engine is None → solo la primera vez:
    #   1. Obtiene la cadena de conexión del proveedor
    #   2. Crea el engine con create_async_engine()
    #      - cadena: "postgresql+asyncpg://postgres:...@localhost:5432/bdfacturas..."
    #      - echo=False: no imprime cada SQL en consola (True útil para debug)
    # Las siguientes llamadas retornan el engine ya creado (reutilización).
    #
    # ¿Qué es un engine?
    # Es un POOL de conexiones a la BD. No es una conexión individual.
    # SQLAlchemy mantiene varias conexiones abiertas y las reutiliza,
    # evitando el costo de abrir/cerrar conexiones constantemente.

        # ================================================================
    # MÉTODOS AUXILIARES — Detección y conversión de tipos
    # ================================================================

    async def _detectar_tipo_columna(
        self, nombre_tabla: str, esquema: str, nombre_columna: str
    ) -> str | None:
        """Consulta information_schema para saber el tipo de una columna."""
        sql = text("""
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = :esquema
            AND table_name = :tabla
            AND column_name = :columna
        """)
        try:
            engine = await self._obtener_engine()
            async with engine.connect() as conn:
                result = await conn.execute(sql, {
                    "esquema": esquema, "tabla": nombre_tabla,
                    "columna": nombre_columna
                })
                row = result.fetchone()
                return row[0].lower() if row else None
        except Exception:
            return None
    # ↑ Consulta los METADATOS de PostgreSQL para saber el tipo de una columna.
    # information_schema.columns es una vista del sistema que describe todas las columnas
    # de todas las tablas. Es estándar SQL (existe en PostgreSQL, MySQL, SQL Server).
    #
    # Ejemplo: _detectar_tipo_columna("producto", "public", "stock")
    #   → Ejecuta: SELECT data_type FROM information_schema.columns
    #              WHERE table_schema='public' AND table_name='producto'
    #              AND column_name='stock'
    #   → Retorna: "integer"
    #
    # ¿Para qué sirve?
    # Cuando el cliente envía {"stock": "20"}, el valor llega como STRING.
    # Pero la columna stock es INTEGER. Necesitamos saber el tipo destino
    # para convertir "20" → 20 antes de hacer el INSERT/UPDATE.
    #
    # Los :parametros (:esquema, :tabla, :columna) son parámetros seguros.
    # SQLAlchemy los reemplaza de forma segura, previniendo SQL injection.
    #
    # async with engine.connect() as conn:
    #   → Obtiene una conexión del pool y la libera automáticamente al salir del bloque.
    # Si ocurre cualquier error, retorna None (la conversión se hará como string).

    def _convertir_valor(self, valor: str, tipo_destino: str | None) -> Any:
        """Convierte un string al tipo Python que corresponde."""
        if tipo_destino is None:
            return valor
        try:
            if tipo_destino in ('integer', 'int4', 'bigint', 'int8',
                                'smallint', 'int2'):
                return int(valor)
            if tipo_destino in ('numeric', 'decimal'):
                return Decimal(valor)
            if tipo_destino in ('real', 'float4', 'double precision', 'float8'):
                return float(valor)
            if tipo_destino in ('boolean', 'bool'):
                return valor.lower() in ('true', '1', 'yes', 'si', 't')
            if tipo_destino == 'uuid':
                return UUID(valor)
            if tipo_destino == 'date':
                return self._extraer_solo_fecha(valor)
            if tipo_destino in ('timestamp without time zone',
                                'timestamp with time zone'):
                return datetime.fromisoformat(valor.replace('Z', '+00:00'))
            if tipo_destino == 'time':
                return time.fromisoformat(valor)
            return valor
        except (ValueError, TypeError):
            return valor
    # ↑ Convierte un STRING al tipo Python que corresponde según el tipo de la columna.
    #
    # ¿Por qué es necesario?
    # Los datos JSON del cliente llegan como strings: {"stock": "20", "valorunitario": "50000.00"}
    # Pero PostgreSQL espera: stock=20 (int), valorunitario=50000.00 (Decimal).
    #
    # Tabla de conversiones:
    # | Tipo PostgreSQL              | Tipo Python | Ejemplo              |
    # |------------------------------|-------------|----------------------|
    # | integer, int4, bigint, int8  | int         | "20" → 20            |
    # | numeric, decimal             | Decimal     | "50000.00" → Decimal  |
    # | real, float4, double         | float       | "3.14" → 3.14        |
    # | boolean, bool                | bool        | "true" → True         |
    # | uuid                         | UUID        | "550e8400-..." → UUID |
    # | date                         | date        | "2024-01-15" → date   |
    # | timestamp                    | datetime    | "2024-01-15T14:30" → datetime |
    # | time                         | time        | "14:30:00" → time     |
    #
    # Si el tipo es None (no se pudo detectar) o la conversión falla,
    # retorna el valor original como string (mejor que lanzar error).
    #
    # Para la tabla producto:
    # - codigo (VARCHAR) → se queda como str
    # - nombre (VARCHAR) → se queda como str
    # - stock (INTEGER) → "20" se convierte a int(20)
    # - valorunitario (NUMERIC) → "50000.00" se convierte a Decimal("50000.00")

    def _extraer_solo_fecha(self, valor: str) -> date:
        """Extrae la parte de fecha de un string ISO."""
        if 'T' in valor:
            return datetime.fromisoformat(
                valor.replace('Z', '+00:00')
            ).date()
        return date.fromisoformat(valor[:10])
    # ↑ Convierte un string de fecha a un objeto date de Python.
    # Si el string incluye hora ("2024-01-15T14:30:00"), extrae solo la fecha.
    # Si es solo fecha ("2024-01-15"), lo convierte directamente.
    # .replace('Z', '+00:00') → convierte formato UTC de JavaScript a ISO Python.
    # valor[:10] → toma solo los primeros 10 caracteres: "2024-01-15".

    def _es_fecha_sin_hora(self, valor: str) -> bool:
        """Detecta si un valor tiene formato YYYY-MM-DD (solo fecha)."""
        return (len(valor) == 10 and valor.count('-') == 2
                and 'T' not in valor)
    # ↑ Verifica si un string es una fecha pura (sin hora).
    # Condiciones: exactamente 10 caracteres, 2 guiones, sin 'T'.
    # "2024-01-15" → True (fecha pura)
    # "2024-01-15T14:30:00" → False (tiene hora)
    # Se usa en _obtener_por_clave para decidir si comparar
    # una columna TIMESTAMP solo por la parte DATE.

    def _serializar_valor(self, valor: Any) -> Any:
        """Convierte tipos Python a tipos serializables para JSON."""
        if isinstance(valor, (datetime, date)):
            return valor.isoformat()
        elif isinstance(valor, Decimal):
            return float(valor)
        elif isinstance(valor, UUID):
            return str(valor)
        return valor
    # ↑ Convierte tipos Python a tipos que JSON puede representar.
    # FastAPI necesita devolver JSON al cliente, pero JSON no tiene
    # tipos nativos para fecha, Decimal o UUID.
    #
    # Conversiones:
    # | Tipo Python | Tipo JSON | Ejemplo                          |
    # |-------------|-----------|----------------------------------|
    # | datetime    | string    | datetime(2024,1,15) → "2024-01-15T00:00:00" |
    # | date        | string    | date(2024,1,15) → "2024-01-15"   |
    # | Decimal     | number    | Decimal('2500000.00') → 2500000.0|
    # | UUID        | string    | UUID('550e...') → "550e8400-..."  |
    # | otros       | sin cambio| "Laptop" → "Laptop", 20 → 20     |
    #
    # isinstance(valor, (datetime, date)) → True si valor es datetime O date.
    # .isoformat() → convierte a string formato ISO 8601.

    # ================================================================
    # OPERACIÓN 1: LISTAR (SELECT * LIMIT n)
    # ================================================================

    async def _obtener_filas(
        self, nombre_tabla: str, esquema: str | None = None,
        limite: int | None = None
    ) -> list[dict[str, Any]]:
        """Obtiene filas de una tabla con LIMIT opcional."""
        if not nombre_tabla or not nombre_tabla.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
        # ↑ Validación: si el nombre de tabla es vacío o solo espacios, error.
        # "not nombre_tabla" captura None y "".
        # "not nombre_tabla.strip()" captura "   " (solo espacios).

        esquema_final = (esquema or "public").strip()
        # ↑ Si esquema es None o vacío, usa "public" (esquema por defecto de PostgreSQL).
        # .strip() elimina espacios en blanco.
        # "or" funciona: si esquema es None/""/"  " (falsy), usa "public".

        limite_final = limite or 1000
        # ↑ Si limite es None o 0, usa 1000 como máximo por defecto.
        # Esto evita traer millones de filas sin querer.

        sql = text(
            f'SELECT * FROM "{esquema_final}"."{nombre_tabla}" LIMIT :limite'
        )
        # ↑ Construye el SQL con f-string para tabla/esquema y :parámetro para LIMIT.
        # Resultado: SELECT * FROM "public"."producto" LIMIT :limite
        #
        # ¿Por qué "comillas dobles"?
        # PostgreSQL usa "comillas dobles" para identificadores (nombres de tablas/columnas).
        # Esto permite nombres con mayúsculas, espacios o palabras reservadas.
        #
        # ¿Por qué :limite y no f-string para el valor?
        # SEGURIDAD: :limite es un parámetro que SQLAlchemy reemplaza de forma segura.
        # Si usáramos f-string para valores, sería vulnerable a SQL injection.
        # Regla: nombres de tabla/esquema en f-string, VALORES siempre con :parametro.

        try:
            engine = await self._obtener_engine()
            # ↑ Obtiene el engine (pool de conexiones). Lazy loading.

            async with engine.connect() as conn:
                # ↑ Obtiene una conexión del pool.
                # "async with" garantiza que la conexión se libere al salir del bloque,
                # incluso si ocurre un error. Es como un try/finally automático.

                result = await conn.execute(sql, {"limite": limite_final})
                # ↑ Ejecuta el SQL con los parámetros.
                # await → espera la respuesta de la BD sin bloquear el hilo.
                # {"limite": limite_final} → reemplaza :limite por el valor (ej: 1000).

                columnas = result.keys()
                # ↑ Obtiene los nombres de las columnas del resultado.
                # Ejemplo: ["codigo", "nombre", "stock", "valorunitario"]

                return [
                    {col: self._serializar_valor(row[i])
                     for i, col in enumerate(columnas)}
                    for row in result.fetchall()
                ]
                # ↑ List comprehension + dict comprehension.
                # result.fetchall() → obtiene TODAS las filas como tuplas.
                # Para cada fila (row), crea un diccionario:
                #   enumerate(columnas) → [(0, "codigo"), (1, "nombre"), (2, "stock"), ...]
                #   row[i] → valor en la posición i de la tupla
                #   self._serializar_valor(row[i]) → convierte Decimal, date, etc. a JSON
                #
                # Ejemplo de transformación:
                #   Fila tupla: ("PR001", "Laptop Lenovo", 20, Decimal('2500000.00'))
                #   → Diccionario: {"codigo": "PR001", "nombre": "Laptop Lenovo",
                #                    "stock": 20, "valorunitario": 2500000.0}

        except Exception as ex:
            raise RuntimeError(
                f"Error PostgreSQL al consultar "
                f"'{esquema_final}.{nombre_tabla}': {ex}"
            ) from ex
        # ↑ Si ocurre cualquier error (conexión, SQL, etc.):
        # - Captura la excepción original (ex)
        # - Lanza una RuntimeError con un mensaje descriptivo
        # - "from ex" conserva la excepción original en la cadena de errores
        #   (útil para depuración: puedes ver el error original en el traceback)

    
        # ================================================================
    # OPERACIÓN 2: BUSCAR POR CLAVE (SELECT * WHERE clave = valor)
    # ================================================================

    async def _obtener_por_clave(
        self, nombre_tabla: str, nombre_clave: str, valor: str,
        esquema: str | None = None
    ) -> list[dict[str, Any]]:
        """Obtiene filas filtradas por una columna y valor."""
        if not nombre_tabla or not nombre_tabla.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
        if not nombre_clave or not nombre_clave.strip():
            raise ValueError("El nombre de la clave no puede estar vacío")
        if not valor or not valor.strip():
            raise ValueError("El valor no puede estar vacío")
        # ↑ Validaciones de entrada: ningún parámetro puede estar vacío.
        # nombre_clave es el nombre de la columna PK (ej: "codigo").
        # valor es el valor a buscar (ej: "PR001").

        esquema_final = (esquema or "public").strip()
        # ↑ Esquema por defecto: "public".

        try:
            tipo_columna = await self._detectar_tipo_columna(
                nombre_tabla, esquema_final, nombre_clave
            )
            # ↑ Consulta information_schema para saber el tipo de la columna PK.
            # Para producto.codigo → retorna "character varying" (VARCHAR).

            # Si buscan una fecha en una columna TIMESTAMP,
            # comparar solo la parte DATE
            if (tipo_columna in ('timestamp without time zone',
                                 'timestamp with time zone')
                    and self._es_fecha_sin_hora(valor)):
                sql = text(f'''
                    SELECT * FROM "{esquema_final}"."{nombre_tabla}"
                    WHERE CAST("{nombre_clave}" AS DATE) = :valor
                ''')
                valor_convertido = self._extraer_solo_fecha(valor)
            # ↑ Caso especial: si la columna es TIMESTAMP pero el usuario busca
            # por fecha sin hora ("2024-01-15"), hace CAST a DATE para comparar
            # solo la parte de fecha. Esto no aplica a producto (no tiene timestamps).
            else:
                sql = text(f'''
                    SELECT * FROM "{esquema_final}"."{nombre_tabla}"
                    WHERE "{nombre_clave}" = :valor
                ''')
                valor_convertido = self._convertir_valor(
                    valor, tipo_columna
                )
            # ↑ Caso normal: SELECT * WHERE "codigo" = :valor
            # Convierte el valor al tipo correcto antes de ejecutar.
            # Para producto: "PR001" → "PR001" (VARCHAR no necesita conversión).

            engine = await self._obtener_engine()
            async with engine.connect() as conn:
                result = await conn.execute(
                    sql, {"valor": valor_convertido}
                )
                columnas = result.keys()
                return [
                    {col: self._serializar_valor(row[i])
                     for i, col in enumerate(columnas)}
                    for row in result.fetchall()
                ]
            # ↑ Ejecuta el SQL, serializa y retorna la lista de diccionarios.
            # Si PR001 existe: [{"codigo": "PR001", "nombre": "Laptop", ...}]
            # Si no existe: [] (lista vacía)

        except Exception as ex:
            raise RuntimeError(
                f"Error PostgreSQL al filtrar "
                f"'{esquema_final}.{nombre_tabla}': {ex}"
            ) from ex

    # ================================================================
    # OPERACIÓN 3: CREAR (INSERT INTO tabla VALUES (...))
    # ================================================================

    async def _crear(
        self, nombre_tabla: str, datos: dict[str, Any],
        esquema: str | None = None
    ) -> bool:
        """Inserta una nueva fila en la tabla."""
        if not nombre_tabla or not nombre_tabla.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
        if not datos:
            raise ValueError("Los datos no pueden estar vacíos")
        # ↑ Validaciones: tabla y datos son obligatorios.
        # datos es un dict como: {"codigo": "PR006", "nombre": "Mouse", "stock": 10, ...}

        esquema_final = (esquema or "public").strip()
        datos_finales = dict(datos)
        # ↑ dict(datos) crea una COPIA del diccionario original.
        # Trabajamos sobre la copia para no modificar el diccionario que nos pasaron.

        columnas = ", ".join(f'"{k}"' for k in datos_finales.keys())
        # ↑ Construye la lista de columnas para el INSERT.
        # datos_finales.keys() → ["codigo", "nombre", "stock", "valorunitario"]
        # f'"{k}"' → envuelve cada nombre en "comillas dobles" (sintaxis PostgreSQL)
        # ", ".join(...) → une con comas: "codigo", "nombre", "stock", "valorunitario"

        parametros = ", ".join(f":{k}" for k in datos_finales.keys())
        # ↑ Construye los placeholders para los valores.
        # :codigo, :nombre, :stock, :valorunitario
        # SQLAlchemy reemplazará cada :placeholder por su valor de forma segura.

        sql = text(
            f'INSERT INTO "{esquema_final}"."{nombre_tabla}" '
            f'({columnas}) VALUES ({parametros})'
        )
        # ↑ SQL final:
        # INSERT INTO "public"."producto"
        # ("codigo", "nombre", "stock", "valorunitario")
        # VALUES (:codigo, :nombre, :stock, :valorunitario)
        #
        # Los valores NO están en el SQL — están como :parámetros seguros.
        # Esto previene SQL injection.

        try:
            valores = {}
            for key, val in datos_finales.items():
                if val is not None and isinstance(val, str):
                    tipo = await self._detectar_tipo_columna(
                        nombre_tabla, esquema_final, key
                    )
                    valores[key] = self._convertir_valor(val, tipo)
                else:
                    valores[key] = val
            # ↑ Para cada campo, detecta el tipo de la columna y convierte el valor.
            # Solo convierte si el valor es un STRING (los que ya son int/float se mantienen).
            # Ejemplo:
            #   "codigo": "PR006" → tipo=VARCHAR → se queda "PR006"
            #   "stock": "10" → tipo=INTEGER → se convierte a int(10)
            #   "stock": 10 → ya es int, no se convierte (no pasa por el if)

            engine = await self._obtener_engine()
            async with engine.begin() as conn:
                result = await conn.execute(sql, valores)
                return result.rowcount > 0
            # ↑ IMPORTANTE: engine.begin() en vez de engine.connect()
            # engine.begin() abre una TRANSACCIÓN:
            #   - Si todo sale bien, hace COMMIT automáticamente al salir del bloque
            #   - Si ocurre un error, hace ROLLBACK automáticamente
            # Esto garantiza que el INSERT sea atómico (todo o nada).
            #
            # result.rowcount → número de filas afectadas por el INSERT.
            # Si es > 0, el INSERT fue exitoso → retorna True.
            # Si es 0, no se insertó nada → retorna False.

        except Exception as ex:
            raise RuntimeError(
                f"Error PostgreSQL al insertar en "
                f"'{esquema_final}.{nombre_tabla}': {ex}"
            ) from ex

    # ================================================================
    # OPERACIÓN 4: ACTUALIZAR (UPDATE tabla SET ... WHERE ...)
    # ================================================================

    async def _actualizar(
        self, nombre_tabla: str, nombre_clave: str, valor_clave: str,
        datos: dict[str, Any], esquema: str | None = None
    ) -> int:
        """Actualiza filas. Retorna filas afectadas."""
        if not nombre_tabla or not nombre_tabla.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
        if not nombre_clave or not nombre_clave.strip():
            raise ValueError("El nombre de la clave no puede estar vacío")
        if not valor_clave or not valor_clave.strip():
            raise ValueError("El valor de la clave no puede estar vacío")
        if not datos:
            raise ValueError("Los datos no pueden estar vacíos")
        # ↑ Validaciones: todos los parámetros son obligatorios para un UPDATE.
        # nombre_clave: nombre de la columna PK (ej: "codigo")
        # valor_clave: valor de la PK del registro a actualizar (ej: "PR001")
        # datos: campos a modificar (ej: {"nombre": "Laptop Gamer", "stock": 15})

        esquema_final = (esquema or "public").strip()
        datos_finales = dict(datos)
        # ↑ Copia del diccionario para no modificar el original.

        clausula_set = ", ".join(
            f'"{k}" = :{k}' for k in datos_finales.keys()
        )
        # ↑ Construye la cláusula SET del UPDATE.
        # datos_finales.keys() → ["nombre", "stock"]
        # f'"{k}" = :{k}' → "nombre" = :nombre, "stock" = :stock
        # Resultado: "nombre" = :nombre, "stock" = :stock

        sql = text(f'''
            UPDATE "{esquema_final}"."{nombre_tabla}"
            SET {clausula_set}
            WHERE "{nombre_clave}" = :valor_clave
        ''')
        # ↑ SQL final:
        # UPDATE "public"."producto"
        # SET "nombre" = :nombre, "stock" = :stock
        # WHERE "codigo" = :valor_clave
        #
        # Nota: la PK usa el nombre fijo :valor_clave para no confundirse
        # con los campos del SET (que usan el nombre de la columna).

        try:
            valores = {}
            for key, val in datos_finales.items():
                if val is not None and isinstance(val, str):
                    tipo = await self._detectar_tipo_columna(
                        nombre_tabla, esquema_final, key
                    )
                    valores[key] = self._convertir_valor(val, tipo)
                else:
                    valores[key] = val
            # ↑ Conversión de tipos para los campos del SET (igual que en _crear).

            tipo_clave = await self._detectar_tipo_columna(
                nombre_tabla, esquema_final, nombre_clave
            )
            valores["valor_clave"] = self._convertir_valor(
                valor_clave, tipo_clave
            )
            # ↑ También convierte el valor de la PK al tipo correcto.
            # Para producto.codigo (VARCHAR): "PR001" → "PR001" (sin cambio).
            # Para una tabla con PK INTEGER: "42" → 42.

            engine = await self._obtener_engine()
            async with engine.begin() as conn:
                result = await conn.execute(sql, valores)
                return result.rowcount
            # ↑ Transacción automática (begin = commit o rollback).
            # result.rowcount → filas afectadas.
            # Si PR001 existe y se actualizó: retorna 1.
            # Si PR001 no existe: retorna 0.

        except Exception as ex:
            raise RuntimeError(
                f"Error PostgreSQL al actualizar "
                f"'{esquema_final}.{nombre_tabla}': {ex}"
            ) from ex

    # ================================================================
    # OPERACIÓN 5: ELIMINAR (DELETE FROM tabla WHERE ...)
    # ================================================================

    async def _eliminar(
        self, nombre_tabla: str, nombre_clave: str, valor_clave: str,
        esquema: str | None = None
    ) -> int:
        """Elimina filas. Retorna filas eliminadas."""
        if not nombre_tabla or not nombre_tabla.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
        if not nombre_clave or not nombre_clave.strip():
            raise ValueError("El nombre de la clave no puede estar vacío")
        if not valor_clave or not valor_clave.strip():
            raise ValueError("El valor de la clave no puede estar vacío")
        # ↑ Validaciones: tabla, clave y valor son obligatorios.

        esquema_final = (esquema or "public").strip()

        sql = text(f'''
            DELETE FROM "{esquema_final}"."{nombre_tabla}"
            WHERE "{nombre_clave}" = :valor_clave
        ''')
        # ↑ SQL: DELETE FROM "public"."producto" WHERE "codigo" = :valor_clave
        # Solo elimina las filas que coincidan con la PK.

        try:
            tipo_clave = await self._detectar_tipo_columna(
                nombre_tabla, esquema_final, nombre_clave
            )
            valor_convertido = self._convertir_valor(
                valor_clave, tipo_clave
            )
            # ↑ Convierte el valor de la PK al tipo correcto.

            engine = await self._obtener_engine()
            async with engine.begin() as conn:
                result = await conn.execute(
                    sql, {"valor_clave": valor_convertido}
                )
                return result.rowcount
            # ↑ Transacción automática.
            # result.rowcount → filas eliminadas.
            # Si PR001 existía: retorna 1.
            # Si PR001 no existía: retorna 0.

        except Exception as ex:
            raise RuntimeError(
                f"Error PostgreSQL al eliminar de "
                f"'{esquema_final}.{nombre_tabla}': {ex}"
            ) from ex
        

        