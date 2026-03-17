"""Modelo Pydantich para la tabla producto."""




from pydantic import BaseModel
# BaseModel es la clase base de Pydantic para modelos de datos.
# Toda clase que herede de BaseModel obtiene:
# - Validación automática de tipos al crear una instancia
# - Método model_dump() para convertir a diccionario
# - Serialización JSON automática
# - Documentación automática en Swagger UI

class Producto(BaseModel):
    """Representa un producto en la base de datos."""
    # Hereda de BaseModel -> obtiene todas las capacidades de Pydantic.
    # Esta clase define 4 campos que correspondan a las 4 columnas
    # de la tabala producto en PostgreSQLL.
    codigo : str
    # Campo obligatorio, tipo string.
    # Corresponde a: producto.codigo VARCHAR(30) NOT NULL
    # Si el cliente no envia "codigo" o envia un número,
    # Pydantic rechaza con error 422.
    # Pydantic convierte automáticamente: 123 -> "123" (coerción a str)

    nombre: str
    # Campo obligatorio, tipo string.
    # Corresponde a: producto.nombre VARCHAR(100) NOT NULL

    stock: int | None = None
    # Campo OPCIONAL, tipo entero o None
    # int | None -> acepta un entero o None (equivale a Optional[int])
    # = None -> valor por defecto si no se envia.
    # Corresponde a: producto.stock INTEGER NOT NULL.
    #
    # ¿Por qué es opcional en el modelo si es NOT NULL en la BD?
    # Porque en un UPDATE puedes querer cambiar solo el nombre,
    # sin enviar stock. El servicio y repositorio manejan qué campos
    # incluir en el SQL.
    #
    # Validación: si envian "abc", Pydantic rechaza con 422.
    # Coerción: si envian "20" (string), Pydantic convierte a int 20

    valorunitario: float | None = None
    # Campo OPCIONAL, tipo decimal o None.
    # float | None -> acepta un número decimal o None.
    # Corresponde a: producto.valorunitario NUMERIC(14,2) NOT NULL
    #
    # Nota: usamos float en el modelo (no Decimal) porque JSON no tiene
    # tipo Decimal. EL repositorio se encarga de la conversión precisa
    # cuando interactúa con PostgreSQL.