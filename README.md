# Pipeline de Gestión de Datos - DataMart Chile S.A.

Sistema integral de procesamiento, validación y almacenamiento de datos para un datamart de ventas en Chile. El objetivo principal es automatizar el flujo de datos desde su ingesta hasta su persistencia en base de datos SQLite, aplicando validaciones estructurales y semánticas en cada etapa del pipeline.

---

## Componentes del Sistema

- **Scripts de procesamiento**: Cuatro etapas de pipeline (ingesta, limpieza, validación y carga) implementadas en Python.
- **Almacenamiento de datos**: Capas de procesamiento en `data/raw`, `data/clean`, `data/validated` y `data/errors`.
- **Validación de datos**: Esquemas con Pandera para validación estructural y reglas de negocio para validación semántica.
- **Base de datos**: SQLite con transacciones, restricciones de integridad y carga controlada.
- **Logging centralizado**: Trazabilidad de cada etapa con archivos de log separados.
- **Documentación**: Guía del flujo completo, estructura de datos y forma de ejecución.

---

## Tecnologías Utilizadas

- Python 3.8+
- Pandas (manipulación y limpieza de datos)
- Pandera (validación de esquemas)
- SQLite3 (persistencia en base de datos)
- Pathlib y os (gestión de rutas y carpetas)
- Logging (auditoría y trazabilidad)
- Git / GitHub

---

## Pipeline Implementado

| Etapa         | Descripción                             | Responsabilidades                                                                                                |
| ------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1. Ingesta    | Carga del archivo CSV de ventas         | Lectura del dataset original, diagnóstico inicial y copia a `data/raw/`                                          |
| 2. Limpieza   | Normalización y transformación de datos | Deduplicación, limpieza de fechas, normalización de precios, categorías y textos, creación de columnas derivadas |
| 3. Validación | Validación estructural y semántica      | Pandera para tipos, rangos y dominios; reglas de negocio para detectar registros inválidos                       |
| 4. Carga      | Persistencia en base de datos SQLite    | Creación de tabla, inserción transaccional, control de rechazos y consultas de verificación                      |

---

## Estructura del Repositorio

```
et_datamart/
├── README.md
├── main.py                       # Orquestador central del pipeline
├── ventas_datamart.csv           # Dataset original de ventas
├── src/
│   ├── ingesta.py                # Etapa 1: lectura y resguardo de datos crudos
│   ├── limpieza.py               # Etapa 2: normalización y transformación
│   ├── validacion.py             # Etapa 3: validación estructural + semántica
│   └── carga.py                  # Etapa 4: carga en SQLite y verificación
└── data/
    ├── raw/                      # Copia cruda del archivo original
    ├── clean/                    # Datos limpios y transformados
    ├── validated/                # Registros que aprobaron validación
    └── errors/                   # Registros rechazados y errores de carga
```

---

## Estructura de Datos

### Tabla base del datamart: pedidos

```
id_pedido, fecha_pedido, rut_cliente, nombre_cliente, region, producto, categoria, cantidad, precio_unitario, descuento_pct, estado_pedido, fecha_despacho
```

### Columnas derivadas en limpieza

```
total_venta, segmento_precio
```

### Salida validada para carga

```
id_pedido, fecha_pedido, rut_cliente, nombre_cliente, region, producto, categoria, cantidad, precio_unitario, descuento_pct, estado_pedido, fecha_despacho, total_venta, segmento_precio
```

---

## Cómo Ejecutar el Sistema

### Prerequisitos

1. **Python 3.8 o superior**

   ```bash
   python --version
   ```

2. **Dependencias instaladas**

   ```bash
   pip install pandas pandera
   ```

3. **Archivo CSV en la raíz del proyecto**
   - `ventas_datamart.csv`

### Ejecución del Pipeline Completo

1. **Clonar el repositorio**

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd et_datamart
   ```

2. **Ejecutar el pipeline de extremo a extremo**

   ```bash
   python main.py
   ```

   Esto ejecuta automáticamente las 4 etapas:
   - Etapa 1: Ingesta
   - Etapa 2: Limpieza y transformación
   - Etapa 3: Validación estructural y semántica
   - Etapa 4: Carga a SQLite

3. **Ejecutar etapas individuales (opcional)**
   ```bash
   python src/ingesta.py
   python src/limpieza.py
   python src/validacion.py
   python src/carga.py
   ```

### Verificar Ejecución

1. **Revisar los logs por etapa**

   ```bash
   type data\raw\ingesta.log
   type data\clean\limpieza.log
   type data\validated\validacion.log
   type data\errors\carga.log
   ```

2. **Verificar archivos de salida**
   - Datos crudos: `data/raw/ventas_raw.csv`
   - Datos limpios: `data/clean/ventas_clean.csv`
   - Datos validados: `data/validated/ventas_validated.csv`
   - Registros rechazados por validación: `data/errors/invalidos.csv`
   - Registros rechazados por BD: `data/errors/rechazados_bd.csv`
   - Base de datos: `ventas.db`

3. **Consultar la base de datos SQLite**
   ```bash
   sqlite3 ventas.db
   > SELECT COUNT(*) FROM pedidos;
   > SELECT region, COUNT(*) FROM pedidos GROUP BY region;
   > SELECT categoria, ROUND(SUM(total_venta), 2) FROM pedidos GROUP BY categoria;
   ```

---

## Validaciones Implementadas

### Validación Estructural (Pandera)

**Campos validados:**

- `id_pedido`: entero único y obligatorio
- `cantidad`: mayor que 0
- `precio_unitario`: mayor que 0
- `descuento_pct`: entre 0 y 100
- `estado_pedido`: valores permitidos `pendiente`, `despachado`, `entregado`, `cancelado`
- `categoria`: valores permitidos `Tecnologia`, `Hogar`, `Moda`

### Validación Semántica (Reglas de Negocio)

- Estado `entregado` debe tener `fecha_despacho`
- `region` no puede venir vacía
- Los registros con errores se separan y se guardan en `data/errors/`

---

## Características ACID Implementadas

| Propiedad        | Implementación                                                                            |
| ---------------- | ----------------------------------------------------------------------------------------- |
| **Atomicidad**   | Inserción controlada dentro de una transacción SQLite con `commit` al final               |
| **Consistencia** | Restricciones de tabla como `PRIMARY KEY` y `NOT NULL` validan integridad de los datos    |
| **Aislamiento**  | La ejecución usa una conexión independiente por corrida                                   |
| **Durabilidad**  | Los cambios quedan persistidos en `ventas.db` solo si la operación concluye correctamente |

---

## Gestión de Errores

### Registros Rechazados

Los registros que no pasan validación se guardan en `data/errors/invalidos.csv` con una columna adicional `motivo_rechazo` que explica por qué fueron descartados.

Si la base de datos rechaza una fila durante la carga, esa fila se guarda en `data/errors/rechazados_bd.csv` con la columna `motivo_rechazo_bd`.

Ejemplo:

```
id_pedido,fecha_pedido,rut_cliente,nombre_cliente,region,producto,categoria,cantidad,precio_unitario,descuento_pct,estado_pedido,fecha_despacho,total_venta,segmento_precio,motivo_rechazo
204,2024-12-17,7489752-5,Cristobal Avila,Valparaiso,Vestido Floral H&M,Moda,-1,9990,23.7,entregado,2024-03-24,-7622.37,bajo,"falla_estructural"
```

### Logs de Auditoría

Cada etapa genera un log con timestamps y detalle de la ejecución:

```
2026-07-09 10:00:00 - INFO - Iniciando la etapa de ingesta...
2026-07-09 10:00:01 - INFO - Fechas normalizadas a YYYY-MM-DD
2026-07-09 10:00:02 - INFO - Validacion estructural: 0 errores.
2026-07-09 10:00:03 - INFO - Transaccion confirmada (COMMIT). Registros insertados: 42.
```

---

## Documentación Técnica

Para detalles profundos sobre la lógica de cada etapa, consulta:

- [main.py](main.py) — Orquestación completa del pipeline
- [src/ingesta.py](src/ingesta.py) — Responsabilidades de la Etapa 1
- [src/limpieza.py](src/limpieza.py) — Transformaciones aplicadas en la Etapa 2
- [src/validacion.py](src/validacion.py) — Esquemas Pandera y reglas de negocio
- [src/carga.py](src/carga.py) — Implementación SQLite y transacciones

---

## Equipo de Desarrollo

- **Gestión de Datos**: Alexander Lambie - Responsable del pipeline y de las transformaciones del datamart
- **QA / Auditoría**: Alan Rodriguez - Responsable de la revisión de validaciones y consistencia
- **DevOps / Deployment**: Greg Astete - Responsable de la ejecución, logs y persistencia local
