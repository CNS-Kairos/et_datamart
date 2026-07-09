"""
ETAPA 3 · VALIDACION
Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce

Carga el dataset limpio (salida de la etapa de limpieza)

"""

import os
import logging
import pandas as pd


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
# ORQUESTADOR DE LA ETAPA DE VALIDACION
# carga el CSV limpio y muestra un diagnostico inicial.
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

        print("\n" + "=" * 60)
        print(" ETAPA 3: VALIDACION — CARGA INICIAL")
        print("=" * 60)
        print(f"Registros cargados : {df.shape[0]}")
        print(f"Columnas           : {df.shape[1]}")
        print("=" * 60 + "\n")

        logger.info("Carga del dataset limpio finalizada.")
        return df

    except Exception as e:
        logger.error(f"Error critico durante la etapa de validacion: {str(e)}")
        raise e


if __name__ == "__main__":
    # Permite ejecutar la etapa de validacion de forma independiente para pruebas
    ejecutar_validacion()