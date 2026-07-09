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