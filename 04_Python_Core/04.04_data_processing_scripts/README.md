# 04.04 Data Processing Scripts

## 📂 Descripción del Proyecto
Este directorio representa la culminación del bloque **Python Core**, donde la lógica de programación se aplica directamente a la resolución de problemas reales de ingeniería y gestión de datos. El enfoque aquí es la **robustez y la integración**: crear scripts que no solo procesen información, sino que lo hagan de forma segura, optimizada y conectada a bases de datos relacionales.

El objetivo es dominar el manejo avanzado de excepciones, la limpieza profunda de strings y la transición hacia la **Programación Orientada a Objetos (OOP)**, preparando el terreno para la construcción del Robot ETL en el siguiente módulo.

---

## 🛠️ Stack Técnico
* **Lenguaje:** Python 3.12.3
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu)
* **Bases de Datos:** SQLite (Chinook DB) 
* **Conceptos Clave:** Resiliencia (Try/Except), OOP, Integración SQL, Optimización de Rendimiento y Carga Masiva (Bulk Load).

---

## 📜 Inventario de Scripts

| # | Nombre del Archivo | Enunciado / Problema Real | Foco Técnico |
| :--- | :--- | :--- | :--- |
| 18 | [`18_robust_data_input.py`](./scripts/18_robust_data_input.py) | Validar entradas del usuario para que el script no se rompa si introducen texto por números. | `Try/Except` |
| 19 | [`19_multi_exception_handler.py`](./scripts/19_multi_exception_handler.py) | Gestionar errores específicos (`ValueError`, `ZeroDivisionError`) en cálculos técnicos. | `Try/Except adv.` |
| 20 | [`20_text_data_cleaner.py`](./scripts/20_text_data_cleaner.py) | **HITO**: Limpiar un archivo de texto masivo eliminando caracteres especiales y normalizando nombres. | `HITO` |
| 21 | [`21_string_cleaning_logic.py`](./scripts/21_string_cleaning_logic.py) | Eliminar espacios y caracteres extraños de una lista de nombres de tracks (Chinook). | `Preparación Datos` |
| 22 | [`22_asset_management_oop.py`](./scripts/22_asset_management_oop.py) | Crear una clase `ElectricMotor` para gestionar datos de activos industriales (potencia, horas). | `OOP` |
| 23 | [`23_sqlite_chinook_check.py`](./scripts/23_sqlite_chinook_check.py) | Conexión básica para verificar que Python "ve" tu base de datos Chinook. | `Integración SQL` |
| 24 | [`24_execution_timer.py`](./scripts/24_execution_timer.py) | Un script que mide cuánto tarda en ejecutarse una función de cálculo pesado. | `Optimización` |
| 25 | [`25_json_schema_validator.py`](./scripts/25_json_schema_validator.py) | Validar la presencia de claves obligatorias en un archivo JSON de configuración técnica. | `Extra (JSON)` |
| 26 | [`26_csv_to_sqlite_bulk.py`](./scripts/26_csv_to_sqlite_bulk.py) | Cargar masivamente datos desde un archivo CSV a una nueva tabla en la base de datos SQLite. | `Extra (Carga)` |
| 27 | [`27_final_core_audit.py`](./scripts/27_final_core_audit.py) | Script que resume todo lo anterior: funciones, lógica, manejo de archivos y errores. | `Consolidación` |

---

## 📈 Hitos de Aprendizaje
1.  **Ingeniería a Prueba de Fallos:** Crear sistemas resilientes que gestionen múltiples tipos de errores sin interrumpir el flujo de datos.
2.  **Limpieza de Datos Masiva:** Aplicación del Hito para la normalización de grandes volúmenes de texto, un paso crítico antes de cualquier proceso de carga.
3.  **Arquitectura Profesional (OOP):** Transición del código procedimental a clases y objetos, permitiendo una gestión escalable de activos industriales.
4.  **Integración de Ecosistemas:** Conexión exitosa entre Python y SQL, dominando la carga de archivos externos (CSV/JSON) hacia bases de datos relacionales.

---
*Este bloque cierra tu formación en Python Core y valida tus habilidades para el Proyecto Final.