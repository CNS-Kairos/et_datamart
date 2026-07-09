"""
ETAPA 3 · VALIDACION
Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce

Carga el dataset limpio (salida de la etapa de limpieza) y aplica la
"""

import os
import logging
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema


# ============================================================
# CONFIGURACION DE LOGGING
# Registra los eventos de la etapa
# ============================================================
def configurar_logger():
    os.makedirs('data/validated', exist_ok=True)
    os.makedirs('data/errors', exist_ok=True)

    logger = logging.getLogger('validacion')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('data/validated/validacion.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


# ============================================================
# VALIDACION ESTRUCTURAL (ESQUEMA PANDERA)
# Reglas de TIPO, RANGO y DOMINIO sobre las columnas.
#
# ============================================================
def construir_esquema_estructural():
    """Devuelve el DataFrameSchema de pandera con las validaciones estructurales."""
    dominio_estado = ['pendiente', 'despachado', 'entregado', 'cancelado']
    dominio_categoria = ['Tecnologia', 'Hogar', 'Moda']

    esquema = DataFrameSchema(
        {
            # 1) id_pedido: entero, obligatorio y UNICO (no deben quedar duplicados)
            'id_pedido': Column(int, nullable=False, unique=True),

            # 2) cantidad: entero estrictamente mayor que 0 (descarta negativos y ceros)
            'cantidad': Column(int, Check.greater_than(0), nullable=False),

            # 3) precio_unitario: numerico mayor que 0 (ya viene limpio, sin '$')
            'precio_unitario': Column(float, Check.greater_than(0), nullable=False),

            # 4) descuento_pct: porcentaje valido dentro del rango [0, 100]
            'descuento_pct': Column(float, Check.in_range(0, 100), nullable=False),

            # 5) estado_pedido: solo valores dentro del dominio permitido
            'estado_pedido': Column(str, Check.isin(dominio_estado), nullable=False),

            # 6) categoria: dominio ya estandarizado en la etapa de limpieza
            'categoria': Column(str, Check.isin(dominio_categoria), nullable=False),
        },
        coerce=True,       # intenta convertir tipos antes de validar
        strict=False,      # permite columnas adicionales (total_venta, segmento_precio, etc.)
    )
    return esquema


def validar_estructura(df, logger):
    """
    Ejecuta el esquema pandera en modo 'lazy' para recolectar TODOS los errores
    a la vez. Devuelve el set de indices de filas que fallan alguna regla
    estructural y un conteo de errores por tipo de check.
    """
    esquema = construir_esquema_estructural()
    indices_invalidos = set()
    conteo_por_check = {}

    try:
        esquema.validate(df, lazy=True)
        logger.info("Validacion estructural: 0 errores. Todos los registros cumplen el esquema.")
    except pa.errors.SchemaErrors as err:
        casos = err.failure_cases

        # Indices de las filas que fallaron (se ignoran chequeos sin indice de fila)
        indices_invalidos = set(
            pd.to_numeric(casos['index'], errors='coerce').dropna().astype(int).tolist()
        )

        # Conteo de errores agrupado por tipo de validacion (columna + check)
        resumen = casos.groupby(['column', 'check']).size()
        for (columna, check), n in resumen.items():
            etiqueta = f"{columna} -> {check}"
            conteo_por_check[etiqueta] = int(n)
            logger.info(f"[ESTRUCTURAL] {etiqueta}: {n} registro(s) invalido(s).")

    return indices_invalidos, conteo_por_check


# ============================================================
# ORQUESTADOR DE LA ETAPA DE VALIDACION
# Encadena: carga -> validacion estructural.
# 
# ============================================================
def ejecutar_validacion(ruta_clean='data/clean/ventas_clean.csv'):
    logger = configurar_logger()
    logger.info("Iniciando la etapa de validacion...")

    try:
        if not os.path.exists(ruta_clean):
            raise FileNotFoundError(
                f"No se encontro el archivo limpio en: {ruta_clean}. "
                "Debe ejecutarse primero la etapa de limpieza."
            )

        # Cargar el dataset limpio y garantizar un indice ordenado (0..n-1)
        df = pd.read_csv(ruta_clean).reset_index(drop=True)
        logger.info(f"Dataset limpio cargado: {df.shape[0]} filas, {df.shape[1]} columnas.")

        # Validacion estructural con pandera
        indices_estructurales, conteo_estructural = validar_estructura(df, logger)

        print("\n" + "=" * 60)
        print(" ETAPA 3: VALIDACION ESTRUCTURAL")
        print("=" * 60)
        print(f"Registros evaluados            : {len(df)}")
        print(f"Registros con fallas estruct.  : {len(indices_estructurales)}")
        print("\nErrores estructurales por tipo:")
        for k, v in conteo_estructural.items():
            print(f"  - {k}: {v}")
        print("=" * 60 + "\n")

        logger.info("Validacion estructural finalizada.")
        return df, indices_estructurales

    except Exception as e:
        logger.error(f"Error critico durante la etapa de validacion: {str(e)}")
        #v2
        raise e


if __name__ == "__main__":
    
    ejecutar_validacion()