"""
main.py - Punto de entrada de la API REST con FastApi.
"""
# Docstring del modulo. Describe el proposito de este archivo.
# ESte es el único archivo que se ejecuta directamente.
# Todos los demás (controllers, servicios, repositorios) son importados.


# ── Importaciones ─────────────────────────────────────────────────────

from fastapi import FastAPI
# FastApi: clase principal del framework
# Crear una instancia de FastApi() es crear la aplicación web completa.
# Esta instancia es el punto central que:
#   - Recibe todas las peticiones HTTP.
#   - Las enruta al controller correcto.
#   - Genera la documentación automatica (Swagger UI y ReDoc)

from controllers.producto_controller import router as producto_router
# Importa el router del controller de productos.
# "router" es el APIRouter definido en producto:controller.py 
# "as producto_router" le da un alias descriptivo.
# Este router contiene los 5 endpoints: GET, GET/{codigo}, POST, PUT, DELETE.


# ── Crear instancia de la aplicacion ──────────────────────────────────

app = FastAPI(
    title="API Producto",
    # Titulo que aparece en Swagger UI (/docs) y ReDoc (/redoc).

    description="API REST CRUS para la tabla producto.",
    # Descripción que aparece debajo del título en la documentación.

    version="1.0.0",
    # Version de la API. Aparece junto al título en /docs.
)
# app es La aplicación. Todo pasa a través de este objeto.
# uvicorn busca este objeto por nombre: uvicorn main(archivo):app(variable)

# ── Registrar el controller ──────────────────────────────────────────

app.include_router(producto_router)
# Conecta el router de productos a la aplicación.
# Esto le dice a FastApi: "todas las rutas definidas en productor_router ahora son parte de esta aplicación"
# Sin esta línea, los endpoints de producto NO existiriían.
# Después de esto, la API tiene 5 endpoints activos:
#   GET    /api/producto/
#   GET    /api/producto/{codigo}
#   POST   /api/producto/
#   PUT    /api/producto/{codigo}
#   DELETE /api/producto/{codigo}


# ── Endpoint raiz ────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
# Decora la función como handler de get /
# tags = ["Root"] -> la agrupa bajo la etiqueta "Root" en Swagger UI.
async def root():
    """Endpoint raíz de verificación"""
    # Sirve para comprobar rapidamente que la API está activa.
    # Es una convención común en APIs REST.
    return {
        "mensaje": "API Producto - activa.",
        #Mensaje de confirmación.
        "docs": "/docs",
        # URL de Swagger UI (documentación interactiva).
        "redoc": "/redoc"
        # URL de ReDoc (documentación alternativa, solo lectura).
    }

    # FastAPI convierte este diccionario a JSON automaticamente.
    # El cliente recibe: {"mensaje": "...", "docs": "/docs", "redoc": "/redoc"}