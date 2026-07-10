"""
ETAPA 4 · CARGA A BASE DE DATOS (SQLite)
Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce

Toma los registros validados (data/validated/ventas_validated.csv), se conecta
a una base SQLite, crea la tabla 'pedidos' con su esquema (PK, tipos, NOT NULL)
y carga los registros dentro de una transaccion ACID (COMMIT / ROLLBACK),
enviando los rechazados por la base a data/errors/rechazados_bd.csv.
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
# CARGA TRANSACCIONAL (ACID)
# Inserta los registros validados dentro de una unica transaccion.
# Si todo sale bien -> COMMIT; ante un error inesperado -> ROLLBACK.
# Las filas que la propia base rechace (PK/NOT NULL) se envian a
# data/errors/rechazados_bd.csv sin abortar el resto de la carga.
# ============================================================
def cargar_datos(conn, df, logger):
    columnas = [
        'id_pedido', 'fecha_pedido', 'rut_cliente', 'nombre_cliente', 'region',
        'producto', 'categoria', 'cantidad', 'precio_unitario', 'descuento_pct',
        'estado_pedido', 'fecha_despacho', 'total_venta', 'segmento_precio'
    ]
    insert_sql = (
        "INSERT INTO pedidos ("
        + ", ".join(columnas)
        + ") VALUES (" + ", ".join(["?"] * len(columnas)) + ")"
    )

    rechazados = []
    insertados = 0

    try:
        for _, fila in df.iterrows():
            # Convertir los NaN de pandas a None para que SQLite los trate como NULL
            valores = tuple(None if pd.isna(fila[c]) else fila[c] for c in columnas)
            try:
                conn.execute(insert_sql, valores)
                insertados += 1
            except sqlite3.IntegrityError as err:
                # La fila viola una restriccion de la tabla (PK duplicada, NOT NULL, etc.)
                registro = fila.to_dict()
                registro['motivo_rechazo_bd'] = str(err)
                rechazados.append(registro)

        # COMMIT: se confirma la transaccion completa
        conn.commit()
        logger.info(f"Transaccion confirmada (COMMIT). Registros insertados: {insertados}.")

    except Exception as err:
        # ROLLBACK: ante cualquier error inesperado se revierte toda la transaccion
        conn.rollback()
        logger.error(f"Error en la carga; se revirtio la transaccion (ROLLBACK): {err}")
        raise

    # Exportar las filas rechazadas por la base de datos
    df_rechazados = pd.DataFrame(rechazados)
    df_rechazados.to_csv(RUTA_RECHAZADOS, index=False)
    logger.info(f"Registros rechazados por la BD: {len(rechazados)} -> {RUTA_RECHAZADOS}")

    return insertados, len(rechazados)


# ============================================================
# ORQUESTADOR DE LA ETAPA DE CARGA
# Encadena: conectar -> crear tabla -> carga transaccional.
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

        # Cargar el dataset validado y asegurar tipos consistentes con el esquema
        df = pd.read_csv(ruta_validados)
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').astype('Int64')
        logger.info(f"Registros validados a cargar: {len(df)}")

        conn = conectar_db(ruta_db, logger)
        crear_tabla(conn, logger)
        insertados, n_rechazados = cargar_datos(conn, df, logger)

        print("\n" + "=" * 60)
        print(" ETAPA 4: CARGA A BASE DE DATOS (SQLite)")
        print("=" * 60)
        print(f"Base de datos          : {ruta_db}")
        print(f"Registros insertados   : {insertados}")
        print(f"Rechazados por la BD   : {n_rechazados}")
        print("=" * 60 + "\n")

        logger.info("Carga transaccional finalizada.")

    except Exception as e:
        logger.error(f"Error critico durante la etapa de carga: {str(e)}")
        raise e
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
   
    ejecutar_carga()