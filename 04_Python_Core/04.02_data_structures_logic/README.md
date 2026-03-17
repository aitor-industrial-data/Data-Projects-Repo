# 04.02 Data Structures & Logic for Data Engineering

## 📂 Descripción del Proyecto
Este directorio marca la transición de la sintaxis básica hacia la **gestión eficiente de colecciones de datos**. Como ingeniero, el enfoque en este módulo es la escalabilidad: pasar de manejar variables únicas a procesar conjuntos masivos de información (sensores, inventarios, configuraciones) mediante estructuras optimizadas.

El objetivo es dominar la organización de datos en memoria, permitiendo que el código sea capaz de filtrar, transformar y consultar información de manera rápida y estructurada, imitando el comportamiento de las bases de datos modernas.

---

## 🛠️ Stack Técnico
* **Lenguaje:** Python 3.12.3
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu) 
* **Herramientas:** Git-bash, DBeaver (referencia para lógica SQL)
* **Conceptos Clave:** Iteración masiva, Mutabilidad vs Inmutabilidad, Mapeo Hash (Key-Value) y Filtrado Declarativo.

---

## 📜 Inventario de Scripts

| # | Nombre del Archivo | Enunciado / Problema Real | Foco Técnico |
| :--- | :--- | :--- | :--- |
| 07 | [`07_batch_process_iterator.py`](./scripts/07_batch_process_iterator.py) | Recorrer una lista de IDs de sensores y aplicar una transformación a cada valor usando un bucle. | `For Loops` |
| 08 | [`08_monitoring_stream_sim.py`](./scripts/08_monitoring_stream_sim.py) | Simular la lectura continua de un sensor hasta que el valor supere un umbral de seguridad. | `While Loops` |
| 09 | [`09_inventory_list_manager.py`](./scripts/09_inventory_list_manager.py) | Crear, añadir y eliminar componentes de una lista de stock de almacén eléctrico (Sistema CRUD). | `List Methods` |
| 10 | [`10_customer_hash_map.py`](./scripts/10_customer_hash_map.py) | Organizar registros de clientes (ID, Name, Email) en un diccionario para búsquedas de tiempo constante. | `Dictionaries` |
| 11 | [`11_config_parser_immutable.py`](./scripts/11_config_parser_immutable.py) | Leer una configuración de sistema guardada en una tupla (inmutable) para proteger la integridad de los datos. | `Tuples` |
| 12 | [`12_sql_style_filtering.py`](./scripts/12_sql_style_filtering.py) | **HITO**: Filtrar una lista de precios superior a la media usando una sola línea de código profesional. | `List Comprehensions` |
| 13 | [`13_config_dict_manager.py`](./scripts/13_config_dict_manager.py) | Gestionar y actualizar un diccionario anidado que simula los parámetros de configuración de un proceso ETL. | `Advanced Dicts` |

---

## 📈 Hitos de Aprendizaje
1.  **Optimización de Colecciones:** Migración de variables individuales a estructuras de datos compuestas, permitiendo el procesamiento de lotes (batches) de información.
2.  **Integridad de Datos:** Aplicación de estructuras inmutables para la protección de configuraciones críticas de hardware y sistema.
3.  **Eficiencia SQL-Style:** Implementación de *List Comprehensions* para realizar transformaciones y filtrados masivos con una sintaxis limpia y de alto rendimiento.
4.  **Gestión de Metadatos:** Manejo de diccionarios anidados para representar estructuras complejas, preparando el camino para el trabajo con JSON y bases de datos NoSQL.

---
*Este módulo es fundamental para el éxito del Proyecto 'Robot ETL' en el Modulo 5. ¡Siguiente paso: Automatización de Sistemas y Librerías Estándar!* 🚀