"""
producto_controller.py - Controller específico para la tabla producto.

Endpoints:
- GET   /api/producto/          -> Listar productos
- GET   /api/producto{codigo}   -> Obtener producto por código
- POST  /api/producto/          -> Crear producto
- PUT   /api/porducto{codigo}   -> Actualizar producto
- DELETE /api/porducto{codigo}  -> Eliminar producto
"""

# Docstring del módulo. Lista los 5 endpoints que este controller exponer.
# Cada endpoint corresponde a una operación CRUD:
#   C = Create(POST)
#   R = Read (GET)
#   U = Update (PUT)
#   D = Delete (DELETE)


from fastapi import APIRouter, HTTPException, Query, Response
# Imports de FastApi:
# APIRouter: crea un grupo de rutas con un prefijo común.
#   Es como un "mini app" que se registra en el app principal.
# HTTPException: lanza errores HTTP con código de estado y detalle.
#   Ejmeplo: HTTPException(status_code=404, detal="No encontrado")
# Query: define parámetros de query string (?esquema=public&limite=10).
#   Permiete documentar y validar parámetros de URL.
# Responde: permite retornar respuestas HTTP personalizadas.
#  Lo usamos para retornar 204 No Content (sin body).

from models.producto import Producto
# Importar el modelo Pydantic. FastApi lo usa para:
# 1. Validar el body de POST y PUT automáticamente
# 2. Generar la documentación en Swagger UI.

from servicios.fabrica_repositorios import crear_servicio_producto
# Importa la fábrica. El controller NUNCA crea repositorios ni
# servicios directamente - siempre usa la fábrica
# EStos mantiene al controller desacoplado de la implementación.


router = APIRouter(prefix="/api/producto", tags = ["Producto"])
# Crea el router con:
# prefix="/api/producto" -> todas las rutas empiezan /api/producto
#   @router.get("/") -> GET /api/producto
#   @router.get("/{codigo}") -> GET /api/producto/PR001
# tags=["Producto"] -> agrupa estos endpoints bajo "Producto" en Swagger UI.
#   Swagger UI muestra los endpoints organizados por tags.

# =========================================================================
# GET /api/producto/ — Listar todos los productos
# =========================================================================

@router.get("/")
# Decorador que registra esta función como handler del GET /api/producto/}
# Cuando el cliente hace GET /api/producto/ , FastApi llama a esta función.
async def listar_productos(
    esquema: str | None = Query(default=None),
    limite: int | None = Query(default=None)
):
    """Lista todos los productos."""
    # Parámetros de query string (van en la URL después del ?):
    # GET /api/producto/?esquema=public&limite=10
    # Quer(default=None) -> el parámetro es opcional, default None.
    # FastApi los documenta automáticamente en Swagger UI.
    # Si el cliente no los envia, ambos son None.
    try:
        servicio = crear_servicio_producto()
        # La fábrica crea el servicio completo:
        # ProveedorConexion -> RepositorioProductoPostgreSQL -> ServicioProducto
        # El controller no sabe qué BD usa.

        filas = await servicio.listar(esquema, limite)
        # await -> espera el resultado sin bloquear.
        # servicio.listar() -> normaliza parámetros -> repo.obtener_todos() -> SQL
        # Retirba: [{"codigo": "PR001", "nombre": "Laptop", ...}, ...]

        if len(filas) == 0:
            return Response(status_code=204)
        # Si no hay productos, retorna 204 No Content (sin body)
        # 204 significa "la petición fue exitosa pero no hay contenido que devolver".
        # Es más correcto que retornar 200 con una lista vacía [].

        return{
            "tabla": "producto",
            "total": len(filas),
            "datos" : filas
        }
        # ↑ Retorna un diccionario que FastAPI convierte a JSON automáticamente.
        # Ejemplo de respuesta:
        # {
        #   "tabla": "producto",
        #   "total": 5,
        #   "datos": [
        #     {"codigo": "PR001", "nombre": "Laptop Lenovo", "stock": 20, "valorunitario": 2500000.0},
        #     {"codigo": "PR002", "nombre": "Monitor Samsung", "stock": 30, "valorunitario": 800000.0},
        #     ...
        #   ]
        # }

    except ValueError as ex:
        raise HTTPException(status_code=400, detail={
            "estado": 400, "mensaje": "Parámetros inválidos", "detalle": str(ex)
        })
    # ValueError viene del servicio (validaciones de negocio).
    # 400 Bad Request = "los datos que enviaste son incorrectos".

    except Exception as ex:
        raise HTTPException(status_code=500, detail={
            "estado": 500, "mensaje": "Error interno del servidor.", "details": str(ex)
        })
    # Cualquier otro error (conexión BD, SQL, etc.).
    # 500 Internal Server Error = "algo salió mal en el servidor".
    # str (ex) incluye el mensaje del error para facilitar el debug.


# =========================================================================
# GET /api/producto/{codigo} — Obtener producto por código
# =========================================================================

@router.get("/{codigo}")
# {codigo} es un PATH PARAMETER: va en la URL, no en query string.
# GET /api/producto/PR001 -> codigo = "PROO1"
# FastApi extraer el valor automáticamente y lo pasa al parámetro 'codigo'.
async def obtener_producto(
    codigo: str,
    esquema: str | None = Query(default=None)
):
    """Obtiene un producto por su codigo."""
    # codigo: str -> viene de la URL (path parameter).
    # esquema -> viene del query string (opcional).

    try:
        servicio = crear_servicio_producto()
        filas = await servicio.obtener_por_codigo(codigo, esquema)
        # Busca el producto por su PK
        # Si PR001 existe: [{"codigo": "PR001", ...}]
        # Si no existe: []

        if len(filas) == 0:
            raise HTTPException(status_code=404, detail={
                "estado": 404,
                "mensaje": f"No se encontró producto con código = {codigo}"
            })
        # Si no encontró el producto, retorna 404 Not Found.
        # 404 = "el recurso que buscas no existe".
        # f".." -> f-string inserta el valor de 'codigo' en el mensaje.

        return{
            "tabla": "producto",
            "total": len(filas),
            "datos": filas
        }


    except HTTPException:
        raise
    # IMPORTANTE: re-lanza las HTTPException que ya creamos arriba (404).
    # Sin este bloque, el except Exception las capturaria y las convertiria
    # en un 500, perdiendo el código 404 original.
    # "raise" sin argumentos re-lanza la misma excepción

    except Exception as ex:
        raise HTTPException(status_code=500, detail={
            "estado" : 500, "mensaje": "Error interno del servidor.", "detalle": str(ex)
        })
    

# =========================================================================
# POST /api/producto/ — Crear producto
# =========================================================================

@router.post("/")
async def crear_producto(
    producto: Producto,
    esquema: str | None=Query(default=None)
):
    """Crea un nuevo producto. Valida con el modelo Pydantic."""
    # producto: Producto -> FastApi espera un JSON en el body de la petición.
    # Pydantic lo valida automáticamente contra el modelo Producto:
    #   -¿Tiene "codigo" (str)? ¿Tiene "nombre" (str)?
    #   -¿"stock" es int o None? ¿"valorunitario" es float o None?
    # Si el JSON es inválido, FastApi retorna 422 SIN ejecutar esta función.
    #
    # esquema -> query string opcional (para seleccionar esquema de BD).
    try:
        datos = producto.model_dump()
        # Convierte el objeto Pydantic a diccionario Python.
        # Producto(codigo = "PR006", nombre="Mouse", stock=10, valorunitario=50000)
        # -> {"codigo": "PR006", "nombre": "Mouse", "stock": 10, "valorunitario": 50000.0}

        servicio = crear_servicio_producto()
        creado = await servicio.crear(datos,esquema)
        # El servicio valida que datos no esté vacio,
        # normaliza el esquema y delega al repositorio.
        # El repositorio ejecuta el INSERT.

        if creado:
            return{
                "estado": 200,
                "mensaje": "Producto creado exitosamente.",
                "datos": datos
            }
        else:
            raise HTTPException(status_code=500, detail={
                "estado": 500, "mensaje": "No se pudo crear el producto."
            })
        # Si el INSERT no afectó filas (raro pero posible).

    except HTTPException:
        raise

    except ValueError as ex:
        raise HTTPException(status_code=400, detail={
            "estado": 400, "mensaje": "Datos inválidos.", "detalle": str(ex)
        })
    except Exception as ex:
        raise HTTPException(status_code=500, detail={
            "estado": 500, "mensaje": "Error interno del servidor.", "detalle": str(ex)
        })


# =========================================================================
# PUT /api/producto/{codigo} — Actualizar producto
# =========================================================================

@router.put("/{codigo}")
async def actualizar_producto(codigo: str, producto: Producto, esquema: str | None=Query(default=None)):
    """Actualiza un producto existente"""
    # ↑ codigo: str → viene de la URL: PUT /api/producto/PR001
    # producto: Producto → viene del body (JSON validado por Pydantic).
    # esquema → query string opcional.
    try:
        datos = producto.model_dump(exclude={"codigo"})
        # IMPORTANTE: exclude = {"codigo"} excluye el campo "codigo" del diccionario.
        # ¿Por qué? Porque el código ya viene en la URL (path paramaeter).
        # No queremeos que el UPDATE intente cambiar la PK.
        # Resultado: {"nombre": "Laptop Gamer", "stock": 15, "valorunitario": 3000000.0}
        
        servicio = crear_servicio_producto()
        filas = await servicio.actualizar(codigo,datos,esquema)
        # servicio.actualizar() valida que codigo y datos no estén vacíos,
        # repo.actualizar() ejecuta: UPDATE producto SET ... WHERE codigo = "PR001"
        # Retorna: número de filas afectadas (0 a 1).

        if filas > 0:
            return{"estado":200,"mensaje": "Producto actualizado exitosamente.", "filtro": f"codigo = {codigo}","Filas afectadas": filas}
        raise HTTPException(status_code=404, detail={"estado": 400, "mensaje": f"No existe producto con código = {codigo}"})
        # Si filas == 0, el producto no existe -> 404.

    except HTTPException:
        raise
    except ValueError as ex:
        raise HTTPException(status_code=400, detail={"estado": 400, "mensaje": "Datos inválidos", "detalle": str(ex)})
    except Exception as ex:
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "Error interno del servidor.", "detalle": str(ex)})
    


# =========================================================================
# DELETE /api/producto/{codigo} — Eliminar producto
# =========================================================================

@router.delete("/{codigo}")
async def eliminar_producto(
    codigo: str,
    esquema: str | None = Query(default=None)
):
    """Elimina un producto por su código."""
    # ↑ codigo → de la URL: DELETE /api/producto/PR001
    # No hay body — DELETE no necesita datos, solo el identificador.
    try:
        servicio = crear_servicio_producto()
        filas = await servicio.eliminar(codigo, esquema)
        # ↑ repo.eliminar() ejecuta: DELETE FROM producto WHERE codigo = 'PR001'
        # Retorna: filas eliminadas (0 o 1).

        if filas > 0:
            return {
                "estado": 200,
                "mensaje": "Producto eliminado exitosamente.",
                "filtro": f"codigo = {codigo}",
                "filasEliminadas": filas
            }
        else:
            raise HTTPException(status_code=404, detail={
                "estado": 404,
                "mensaje": f"No existe producto con codigo = {codigo}"
            })

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail={
            "estado": 500, "mensaje": "Error interno del servidor.", "detalle": str(ex)
        })