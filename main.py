# Para que encuentre 'src' y pueda importar los scripts de cada etapa
import sys

# Importar las funciones de las etapas del pipeline
from src.ingesta import ejecutar_ingesta
from src.limpieza import ejecutar_limpieza

def main():
    print("============================================================")
    print(" INICIANDO PIPELINE DE DATOS: DATAMART CHILE S.A.")
    print("============================================================\n")
    
    try:
        # Etapa 1: Ingesta
        print("[PIPELINE] Ejecutando Etapa 1: Ingesta de datos...")
        df_raw = ejecutar_ingesta('ventas_datamart.csv')
        print("[PIPELINE] Etapa 1 finalizada con éxito.\n")
        

        # Etapa 2: Limpieza y Transformación (Placeholder)
        print("[PIPELINE] Etapa 2: Limpieza y Transformación -> ESPERANDO INTEGRACIÓN")
        df_clean = ejecutar_limpieza()
        print("[PIPELINE] Etapa 2 finalizada con éxito.\n")
        
        # Etapa 3: Validación (Placeholder)
        print("[PIPELINE] Etapa 3: Validación con Pandera -> ESPERANDO INTEGRACIÓN")
        print("-" * 60 + "\n")
        
        # Etapa 4: Carga a Base de Datos (Placeholder)
        print("[PIPELINE] Etapa 4: Carga a BD (SQLite) -> ESPERANDO INTEGRACIÓN")
        print("-" * 60 + "\n")
        
        print("============================================================")
        print(" PIPELINE EJECUTADO PARCIALMENTE (ETAPA 1 COMPLETADA)")
        print("============================================================")

    except Exception as e:
        print(f"\n[PIPELINE ERROR] El flujo se detuvo debido a un fallo: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()