"""
ETAPA 4 · CARGA A BASE DE DATOS (SQLite)
Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce

Toma los registros validados (data/validated/ventas_validated.csv), se conecta
a una base SQLite y crea la tabla 'pedidos' con su esquema (PK, tipos, NOT NULL).
"""

import os
import logging
import sqlite3
import pandas as pd

# Rutas de la etapa 
RUTA_VALIDADOS = 'data/validated/ventas_validated.csv'
RUTA_DB = 'ventas.db'
RUTA_RECHAZADOS = 'data/errors/rechazados_bd.csv'


# ============================================================
# CONFIGURACION DE LOGGING
# Registra los eventos de la etapa 
# ============================================================
def configurar_logger():
    os.makedirs('data/errors', exist_ok=True)

    logger = logging.getLogger('carga')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('data/errors/carga.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


# ============================================================
# CONEXION A LA BASE DE DATOS
# Abre (o crea) el archivo SQLite y devuelve la conexion.
# ============================================================
def conectar_db(ruta_db, logger):
    conn = sqlite3.connect(ruta_db)
    logger.info(f"Conexion establecida con la base de datos: {ruta_db}")
    return conn


# ============================================================
# CREACION DE LA TABLA 'pedidos'
# Esquema explicito: clave primaria, tipos por columna y NOT NULL
# en los campos obligatorios del negocio.
# ============================================================
def crear_tabla(conn, logger):
    # Se recrea la tabla para que la carga sea reproducible en cada ejecucion
    conn.execute("DROP TABLE IF EXISTS pedidos")
    conn.execute("""
        CREATE TABLE pedidos (
            id_pedido        INTEGER PRIMARY KEY,
            fecha_pedido     TEXT,
            rut_cliente      TEXT,
            nombre_cliente   TEXT,
            region           TEXT    NOT NULL,
            producto         TEXT,
            categoria        TEXT    NOT NULL,
            cantidad         INTEGER NOT NULL,
            precio_unitario  REAL    NOT NULL,
            descuento_pct    REAL    NOT NULL,
            estado_pedido    TEXT    NOT NULL,
            fecha_despacho   TEXT,
            total_venta      REAL    NOT NULL,
            segmento_precio  TEXT
        )
    """)
    conn.commit()
    logger.info("Tabla 'pedidos' creada con su esquema (PK, tipos y NOT NULL).")


# ============================================================
# ORQUESTADOR DE LA ETAPA DE CARGA
# Por ahora: conectar -> crear tabla.
# (La carga transaccional y la consulta se agregan en los siguientes commits.)
# ============================================================
def ejecutar_carga(ruta_validados=RUTA_VALIDADOS, ruta_db=RUTA_DB):
    logger = configurar_logger()
    logger.info("Iniciando la etapa de carga a base de datos...")

    conn = None
    try:
        if not os.path.exists(ruta_validados):
            raise FileNotFoundError(
                f"No se encontro el archivo validado en: {ruta_validados}. "
                "Debe ejecutarse primero la etapa de validacion."
            )

        conn = conectar_db(ruta_db, logger)
        crear_tabla(conn, logger)

        print("\n" + "=" * 60)
        print(" ETAPA 4: CARGA — CONEXION Y ESQUEMA")
        print("=" * 60)
        print(f"Base de datos      : {ruta_db}")
        print("Tabla 'pedidos'    : creada")
        print("=" * 60 + "\n")

        logger.info("Conexion y creacion de tabla finalizadas.")

    except Exception as e:
        logger.error(f"Error critico durante la etapa de carga: {str(e)}")
        raise e
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    # Permite ejecutar la etapa de carga de forma independiente para pruebas
    ejecutar_carga()