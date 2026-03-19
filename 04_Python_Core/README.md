# 04_ Python Core: Fundamentos para Ingeniería de Datos

Este repositorio contiene una suite avanzada de módulos y scripts de Python diseñados para establecer una base programática robusta, orientada a la **automatización de procesos industriales** y la **arquitectura de tuberías de datos (ETL)**. El enfoque principal de este módulo es la transición de scripts funcionales simples hacia código profesional, modular, escalable y preparado para entornos de producción.

## 🛠️ Stack Tecnológico y Entorno
* **Lenguaje:** Python 3.12.3
* **Gestión de Datos:** SQLite (Integración con base de datos Chinook)
* **Entorno de Desarrollo:** Visual Studio Code + WSL2 (Ubuntu), Docker Desktop.
* **Librerías Core:** `math`, `datetime`, `os`, `sys`, `json`, `sqlite3`.
* **Control de Versiones:** Git / GitHub.

---

## 📂 Arquitectura del Módulo

El proyecto se divide en cuatro capas estratégicas que cubren desde la sintaxis base hasta la integración con bases de datos y programación orientada a objetos (OOP).

### [04.01] Python Foundations
* **Enfoque:** Tipos de datos complejos, manipulación de strings y lógica de decisión técnica.
* **Destacado:** Implementación de formateadores de rutas multiplataforma y lógica de seguridad para rangos de presión industrial.

### [04.02] Data Structures & Logic
* **Enfoque:** Estructuras de datos avanzadas (Diccionarios, Tuplas, Listas) y eficiencia algorítmica.
* **Destacado:** Uso de *List Comprehensions* para filtrado de datos con lógica de estilo SQL.

### [04.03] System Automation Lab
* **Enfoque:** Interacción directa con el sistema operativo y persistencia de datos.
* **Destacado:** Automatizador de organización de archivos masivos y generadores de logs para auditoría de sistemas.

### [04.04] Data Processing Scripts
* **Enfoque:** Integración SQL, manejo de errores profesional (Try/Except) y OOP.
* **Destacado:** Conexión y carga masiva de datos (CSV a SQLite) y modelado de activos industriales mediante clases.

---

## 🚀 Implementaciones Técnicas Clave

| Capacidad | Descripción Técnica |
| :--- | :--- |
| **Lógica Industrial** | Scripts para el cálculo de caída de tensión, conversión de unidades técnicas y validación de sensores. |
| **Robustez de Código** | Gestión avanzada de excepciones para evitar rupturas en la ejecución de procesos de datos. |
| **Optimización** | Uso de iteradores y estructuras inmutables para garantizar el rendimiento en el procesamiento de listas de sensores. |
| **Integración SQL** | Puente directo entre lógica Python y bases de datos relacionales para validación de esquemas. |

---

## 📋 Inventario de Scripts Principales

| ID | Script | Foco Técnico | Aplicación Real |
| :--- | :--- | :--- | :--- |
| 06 | [`voltage_drop_calculator.py`](./04.01_python_foundations/scripts/06_voltage_drop_calculator.py) | Funciones I | Cálculo de caída de tensión basado en longitud, sección y material. |
| 15 | [`automated_folder_sorter.py`](./04.03_system_automation_lab/scripts/15_automated_folder_sorter.py) | Automatización OS | Clasificación automática de datasets por extensión (.csv, .json, .log). |
| 20 | [`text_data_cleaner.py`](./04.04_data_processing_scripts/scripts/20_text_data_cleaner.py) | Limpieza de Datos | Normalización de strings y eliminación de caracteres especiales en archivos masivos. |
| 22 | [`asset_management_oop.py`](./04.04_data_processing_scripts/scripts/22_asset_management_oop.py) | OOP Avanzado | Gestión de activos (motores eléctricos) mediante clases, potencia y horas de uso. |
| 26 | [`csv_to_sqlite_bulk.py`](./04.04_data_processing_scripts/scripts/26_csv_to_sqlite_bulk.py.py) | Carga de Datos | Ingestión masiva de registros CSV hacia tablas estructuradas en SQLite. |

---
*Nota de Ingeniería: Este módulo constituye el motor lógico para el desarrollo posterior de herramientas de extracción web y orquestación de datos en la nube. El código sigue los estándares de legibilidad y documentación técnica necesarios para un perfil de Data Engineer profesional.*