# =============================================================================
# ETAPA 2 — LIMPIEZA Y TRANSFORMACIÓN
# Caso: DataMart Chile S.A. — Pipeline de Datos E-Commerce
# =============================================================================

import re
import logging
import pandas as pd
from pathlib import Path

# ─── Rutas del proyecto (relativas al directorio de ejecución) ───────────────
BASE_DIR = Path.cwd()
RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "clean"

# Crear directorios si no existen
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger('limpieza')
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(CLEAN_DIR / 'limpieza.log', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


# ─── Funciones de limpieza ─────────────────────────────────────────────────

def parsear_fecha(serie):
    """Convierte fechas en múltiples formatos a ISO (YYYY-MM-DD)."""
    fechas = pd.to_datetime(serie, format='mixed', dayfirst=True, errors='coerce')
    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
        mask = fechas.isna()
        if mask.any():
            fechas[mask] = pd.to_datetime(serie[mask], format=fmt, errors='coerce')
    return fechas.dt.strftime('%Y-%m-%d')


def limpiar_precio(valor):
    """Elimina '$' y puntos de miles, convierte a float."""
    if pd.isna(valor):
        return None
    s = str(valor).strip().replace('$', '').replace('.', '')
    try:
        return float(s) if s else None
    except ValueError:
        return None


def estandarizar_categoria(valor):
    """Estandariza categorías (tech/tecnologia→Tecnologia, hogar→Hogar, moda→Moda)."""
    if pd.isna(valor):
        return None
    s = str(valor).strip().lower()
    mapeo = {'tech': 'Tecnologia', 'tecnologia': 'Tecnologia', 'tecnología': 'Tecnologia',
             'hogar': 'Hogar', 'moda': 'Moda'}
    return mapeo.get(s, s.title())


def limpiar_nombre(nombre):
    """Capitaliza y elimina espacios extra."""
    if pd.isna(nombre):
        return None
    return str(nombre).strip().title()


def limpiar_rut(rut):
    """Normaliza el RUT a formato sin puntos y con guión: 12345678-9."""
    if pd.isna(rut) or str(rut).strip() == '':
        return None
    r = re.sub(r'[^0-9kK]', '', str(rut)).upper()   # deja solo dígitos y K
    if len(r) < 2:
        return None
    return f"{r[:-1]}-{r[-1]}"                        # cuerpo + guión + dígito verificador


def ejecutar_limpieza(
    ruta_origen: str = None,
    ruta_destino: str = None
):
    """
    Ejecuta la limpieza completa sobre ventas_raw.csv.
    """
    if ruta_origen is None:
        ruta_origen = RAW_DIR / 'ventas_raw.csv'
    if ruta_destino is None:
        ruta_destino = CLEAN_DIR / 'ventas_clean.csv'

    logger.info("=" * 60)
    logger.info("INICIO Etapa 2 — Limpieza y Transformación")
    logger.info("=" * 60)

    try:
        # 1. Cargar datos
        logger.info(f"Cargando datos desde: {ruta_origen}")
        df = pd.read_csv(ruta_origen, dtype=str, keep_default_na=False)
        logger.info(f"Filas iniciales: {len(df)}")

        # 2. Duplicados
        duplicados_iniciales = df.duplicated(subset=['id_pedido']).sum()
        df = df.drop_duplicates(subset=['id_pedido'], keep='first')
        logger.info(f"Duplicados eliminados: {duplicados_iniciales}")

        # 3. Fechas
        df['fecha_pedido'] = parsear_fecha(df['fecha_pedido'])
        df['fecha_despacho'] = parsear_fecha(df['fecha_despacho'])
        logger.info("Fechas normalizadas a YYYY-MM-DD")

        # 4. Precio
        df['precio_unitario'] = df['precio_unitario'].apply(limpiar_precio)
        logger.info("Precio unitario limpiado")

        # 5. Categoría
        df['categoria'] = df['categoria'].apply(estandarizar_categoria)
        logger.info("Categorías estandarizadas")

        # 6. Textos y RUT
        df['producto'] = df['producto'].str.strip()
        df['nombre_cliente'] = df['nombre_cliente'].apply(limpiar_nombre)
        df['rut_cliente'] = df['rut_cliente'].apply(limpiar_rut)
        logger.info("Textos y RUT normalizados")

        # 7. Conversión numérica
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')
        df['descuento_pct'] = pd.to_numeric(df['descuento_pct'], errors='coerce')

        # 8. Columna derivada: total_venta
        df['total_venta'] = (
            df['cantidad'] * df['precio_unitario'] * (1 - df['descuento_pct'] / 100)
        ).round(2)
        logger.info("Columna 'total_venta' creada")

        # 9. Columna derivada: segmento_precio
        df['segmento_precio'] = pd.cut(
            df['precio_unitario'],
            bins=[-float('inf'), 10000, 50000, float('inf')],
            labels=['bajo', 'medio', 'alto'],
            right=False
        )
        logger.info("Columna 'segmento_precio' creada")

        # 10. Guardar
        df.to_csv(ruta_destino, index=False, encoding='utf-8')
        logger.info(f"Datos limpios guardados en: {ruta_destino}")
        logger.info(f"Filas finales: {len(df)}")
        logger.info("=" * 60)
        logger.info("FIN Etapa 2 — Limpieza y Transformación")
        logger.info("=" * 60)

        return df

    except Exception as e:
        logger.error(f"Error crítico en limpieza: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    ejecutar_limpieza()