import os
import pandas as pd
import logging


def ejecutar_ingesta(ruta_origen='ventas_datamart.csv'):
    # Crear directorios locales para almacenar los datos crudos y los archivos de registro
    os.makedirs('data/raw', exist_ok=True)
    
    # Configurar el sistema de registro de eventos para la etapa de ingesta
    logger = logging.getLogger('ingesta')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = logging.FileHandler('data/raw/ingesta.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.info("Iniciando la etapa de ingesta...")

    try:
        # Verificar si el archivo original existe en la ruta especificada
        if not os.path.exists(ruta_origen):
            raise FileNotFoundError(f"No se encontró el archivo original en la ruta: {ruta_origen}")
            
        # Cargar el dataset interpretando todas las columnas como cadenas de texto
        df = pd.read_csv(ruta_origen, dtype=str)

        print("\n" + "="*60)
        print(" DIAGNÓSTICO ESTADÍSTICO INICIAL (ETAPA 1: INGESTA)")
        print("="*60)
        print(f"Dimensiones del DataFrame: {df.shape}")
        print("\nTipos de datos por columna: ")
        print(df.dtypes)
        print("\nEstructura general del DataFrame: ")
        df.info()
        print("\nConteo de valores nulos por columna: ")
        print(df.isnull().sum())
        print("="*60 + "\n")
        
        # Guardar la copia exacta del archivo original en la ruta de datos crudos
        ruta_destino = 'data/raw/ventas_raw.csv'
        df.to_csv(ruta_destino, index=False)
        logger.info(f"Copia intacta guardada en: {ruta_destino}")
        
        # Registrar metadatos finales del procesamiento en el archivo log
        logger.info(f"Archivo fuente procesado: {ruta_origen}")
        logger.info(f"Registros totales cargados: {len(df)}")
        logger.info("Etapa de ingesta finalizada exitosamente.")
        return df
    
    except Exception as e:
        # Capturar cualquier fallo en el proceso, registrarlo en el log y relanzar el error
        logger.error(f"Error crítico durante la etapa de ingesta: {str(e)}")
        raise e

if __name__ == "__main__":
    # Permitir la ejecución directa del archivo para pruebas individuales
    ejecutar_ingesta()