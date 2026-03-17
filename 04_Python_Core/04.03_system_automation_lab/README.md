# 04.03 System Automation & Lab

## 📂 Descripción del Proyecto
Este directorio marca el inicio de la **automatización operativa** dentro del sistema. Como ingeniero, el enfoque en este bloque se desplaza desde la lógica pura en memoria hacia la interacción con el sistema de archivos del sistema operativo. Se busca construir herramientas que gestionen la persistencia de datos y la organización de activos digitales de forma autónoma.

El objetivo es dominar las librerías estándar de Python que permiten al código "hablar" con el PC, permitiendo la generación de reportes automáticos, la orquestación de archivos por tipos y la aplicación de precisión matemática en cálculos de ingeniería.

---

## 🛠️ Stack Técnico
* **Lenguaje:** Python 3.12.3 
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu) 
* **Librerías Estándar:** `os`, `shutil`, `math`, `datetime`.
* **Conceptos Clave:** Escritura de Archivos (I/O), Automatización de Directorios, Marcas de Tiempo y Persistencia Plana.

---

## 📜 Inventario de Scripts

| # | Nombre del Archivo | Enunciado / Problema Real | Foco Técnico |
| :--- | :--- | :--- | :--- |
| 14 | [`14_log_report_generator.py`](./scripts/14_log_report_generator.py) | Crear un script que escriba un resumen de eventos diarios en un archivo `daily_log.txt`. | `Escritura Archivos` |
| 15 | [`15_automated_folder_sorter.py`](./scripts/15_automated_folder_sorter.py) | **HITO**: Mover archivos de una carpeta a otras (ej. .csv a /data) según su extensión de forma automática. | `HITO` |
| 16 | [`16_math_precision_module.py`](./scripts/16_math_precision_module.py) | Usar la librería `math` y `datetime` para calcular tiempos de ejecución y redondeos técnicos de alta precisión. | `Librerías Estándar` |
| 17 | [`17_list_to_txt_export.py`](./scripts/17_list_to_txt_export.py) | Exportar una lista de resultados de ingeniería a un archivo `.txt` plano para asegurar la persistencia. | `Persistencia` |

---

## 📈 Hitos de Aprendizaje
1.  **Automatización de FileSystem:** Implementación del Hito para la gestión autónoma de grandes volúmenes de archivos, base necesaria para la ingesta de datos en pipelines reales.
2.  **Registro de Eventos (Logging):** Creación de logs para la trazabilidad de procesos, fundamental para el monitoreo de tareas desatendidas en el futuro Robot ETL.
3.  **Precisión de Ingeniería:** Integración de módulos matemáticos y temporales para estandarizar resultados y medir el rendimiento de los scripts desarrollados.
4.  **Persistencia de Salida:** Desarrollo de capacidades para exportar colecciones de datos de Python a formatos legibles externos (.txt), permitiendo la comunicación entre sistemas.

---
*Este bloque es el puente directo hacia la robustez y el manejo de errores del siguiente nivel. ¡Siguiente paso: Gestión de Excepciones y Limpieza de Datos Masivos!* 🚀