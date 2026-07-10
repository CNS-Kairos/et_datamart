# main.py — Orquestador del pipeline DataMart Chile S.A.
# Ejecuta las 4 etapas en orden: Ingesta -> Limpieza -> Validacion -> Carga
import sys

# Importar las funciones de las etapas del pipeline
from src.ingesta import ejecutar_ingesta
from src.limpieza import ejecutar_limpieza
from src.validacion import ejecutar_validacion
from src.carga import ejecutar_carga


def main():
    print("============================================================")
    print(" INICIANDO PIPELINE DE DATOS: DATAMART CHILE S.A.")
    print("============================================================\n")

    try:
        # Etapa 1: Ingesta
        print("[PIPELINE] Ejecutando Etapa 1: Ingesta de datos...")
        ejecutar_ingesta('ventas_datamart.csv')
        print("[PIPELINE] Etapa 1 finalizada con éxito.\n")

        # Etapa 2: Limpieza y Transformación
        print("[PIPELINE] Ejecutando Etapa 2: Limpieza y Transformación...")
        ejecutar_limpieza()
        print("[PIPELINE] Etapa 2 finalizada con éxito.\n")

        # Etapa 3: Validación (estructural + semántica con pandera)
        print("[PIPELINE] Ejecutando Etapa 3: Validación con Pandera...")
        ejecutar_validacion()
        print("[PIPELINE] Etapa 3 finalizada con éxito.\n")

        # Etapa 4: Carga a Base de Datos (SQLite)
        print("[PIPELINE] Ejecutando Etapa 4: Carga a BD (SQLite)...")
        ejecutar_carga()
        print("[PIPELINE] Etapa 4 finalizada con éxito.\n")

        print("============================================================")
        print(" PIPELINE EJECUTADO COMPLETAMENTE (ETAPAS 1 A 4)")
        print("============================================================")

    except Exception as e:
        print(f"\n[PIPELINE ERROR] El flujo se detuvo debido a un fallo: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()