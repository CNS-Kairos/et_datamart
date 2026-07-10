"""
ETAPA 3 · VALIDACION
Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce

Carga el dataset limpio (salida de la etapa de limpieza) y aplica la
validacion estructural con un esquema pandera (tipos, rangos y dominios)
y la validacion semantica (reglas de negocio), separa los registros validos
de los invalidos y exporta cada grupo a su carpeta con trazabilidad en el log.
"""

import os
import logging
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema


# ============================================================
# CONFIGURACION DE LOGGING
# Registra los eventos de la etapa tanto en archivo como en consola.
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
# VALIDACION SEMANTICA (REGLAS DE NEGOCIO)
# Reglas que dependen de la logica del negocio, no solo del tipo de dato.
# ============================================================
def validar_semantica(df, logger):
    """
    Aplica las reglas de negocio y devuelve un diccionario indice -> lista de
    motivos, ademas del conteo por regla para el log.
    """
    motivos = {}
    conteo_por_regla = {}

    def registrar(mascara, etiqueta):
        idxs = df.index[mascara].tolist()
        conteo_por_regla[etiqueta] = len(idxs)
        for i in idxs:
            motivos.setdefault(i, []).append(etiqueta)
        logger.info(f"[SEMANTICA] {etiqueta}: {len(idxs)} registro(s) invalido(s).")

    # Regla 1: un pedido 'entregado' DEBE tener fecha_despacho (no nula ni vacia)
    fecha_vacia = df['fecha_despacho'].isna() | (df['fecha_despacho'].astype(str).str.strip() == '')
    regla_1 = (df['estado_pedido'].astype(str).str.lower() == 'entregado') & fecha_vacia
    registrar(regla_1, "entregado_sin_fecha_despacho")

    # Regla 2: la region de despacho no puede quedar sin asignar (nula o vacia)
    region_vacia = df['region'].isna() | (df['region'].astype(str).str.strip() == '')
    registrar(region_vacia, "region_nula")

    return motivos, conteo_por_regla


# ============================================================
# SEPARACION Y EXPORTACION DE RESULTADOS
# Cruza los resultados estructurales y semanticos, separa validos e invalidos
# y exporta cada grupo a su carpeta correspondiente.
# ============================================================
def separar_y_exportar(df, indices_estructurales, motivos_semanticos, logger):
    # Union de todos los indices que fallaron cualquier validacion
    indices_invalidos = set(indices_estructurales) | set(motivos_semanticos.keys())

    df_validos = df.drop(index=indices_invalidos).copy()
    df_invalidos = df.loc[sorted(indices_invalidos)].copy()

    # Construir columna 'motivo_rechazo' explicando por que se rechazo cada fila
    def construir_motivo(idx):
        motivos = []
        if idx in indices_estructurales:
            motivos.append("falla_estructural")
        motivos.extend(motivos_semanticos.get(idx, []))
        return "; ".join(motivos)

    if not df_invalidos.empty:
        df_invalidos['motivo_rechazo'] = [construir_motivo(i) for i in df_invalidos.index]

    ruta_validos = 'data/validated/ventas_validated.csv'
    ruta_invalidos = 'data/errors/invalidos.csv'
    df_validos.to_csv(ruta_validos, index=False)
    df_invalidos.to_csv(ruta_invalidos, index=False)

    logger.info(f"Registros validos guardados en: {ruta_validos} ({len(df_validos)} filas).")
    logger.info(f"Registros invalidos guardados en: {ruta_invalidos} ({len(df_invalidos)} filas).")

    return df_validos, df_invalidos


# ============================================================
# ORQUESTADOR DE LA ETAPA DE VALIDACION
# Encadena: carga -> estructural -> semantica -> separacion/exportacion.
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

        # Validacion semantica (reglas de negocio)
        motivos_semanticos, conteo_semantico = validar_semantica(df, logger)

        # Separacion de validos/invalidos y exportacion a sus carpetas
        df_validos, df_invalidos = separar_y_exportar(
            df, indices_estructurales, motivos_semanticos, logger
        )

        print("\n" + "=" * 60)
        print(" RESUMEN DE VALIDACION (ETAPA 3)")
        print("=" * 60)
        print(f"Registros totales evaluados : {len(df)}")
        print(f"Registros VALIDOS           : {len(df_validos)}")
        print(f"Registros INVALIDOS         : {len(df_invalidos)}")
        print("\nErrores estructurales por tipo:")
        for k, v in conteo_estructural.items():
            print(f"  - {k}: {v}")
        print("\nErrores semanticos por regla:")
        for k, v in conteo_semantico.items():
            print(f"  - {k}: {v}")
        print("=" * 60 + "\n")

        logger.info("Etapa de validacion finalizada exitosamente.")
        return df_validos, df_invalidos

    except Exception as e:
        logger.error(f"Error critico durante la etapa de validacion: {str(e)}")
        raise e


if __name__ == "__main__":
    ejecutar_validacion()