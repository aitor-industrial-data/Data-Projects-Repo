# 04.01 Python Foundations for Industrial Engineering

## 📂 Descripción del Proyecto
Este directorio contiene los pilares fundamentales de mi aprendizaje en Python. Como **Ingeniero Técnico Industrial** en transición hacia la **Ingeniería de Datos**, estos scripts están diseñados para cerrar la brecha entre la lógica industrial física y el procesamiento programático de datos.

El objetivo de este módulo es dominar la sintaxis core de Python, aplicando reglas de negocio técnicas y preparando el entorno para pipelines de datos robustos en el futuro.

---

## 🛠️ Stack Técnico
* **Lenguaje:** Python 3.12.3
* **Entorno:** Visual Studio Code con WSL2 (Ubuntu) 
* **Herramientas:** Git-bash para control de versiones 
* **Conceptos Clave:** Tipado de datos, Manipulación de Strings, Lógica de Control de Flujo y Modularización mediante Funciones.

---

## 📜 Inventario de Scripts

| # | Nombre del Archivo | Enunciado / Problema Real | Foco Técnico |
| :--- | :--- | :--- | :--- |
| 01 | [`01_industrial_sensor_data.py`](./scripts/01_industrial_sensor_data.py) | Definir variables para temperatura, presión y estado de una máquina; realizar conversiones de tipos. | `Variables` / `Types` |
| 02 | [`02_string_path_formatter.py`](./scripts/02_string_path_formatter.py) | Formatear rutas de carpetas de Windows a formato Linux/WSL usando métodos de strings. | `String Methods` |
| 03 | [`03_safety_margin_check.py`](./scripts/03_safety_margin_check.py) | Evaluar si una lectura de presión industrial está en rango 'Safe', 'Warning' o 'Critical'. | `if` / `elif` / `else` |
| 04 | [`04_login_retry_logic.py`](./scripts/04_login_retry_logic.py) | Simular un sistema de acceso que permite máximo 3 intentos fallidos antes de bloquearse. | `Loops` / `Logic` |
| 05 | [`05_unit_converter_tool.py`](./scripts/05_unit_converter_tool.py) | Crear funciones que conviertan unidades (ej. kW a HP) para reutilizarlas en cálculos técnicos. | `Functions` |
| 06 | [`06_voltage_drop_calculator.py`](./scripts/06_voltage_drop_calculator.py) | **HITO**: Calcular la caída de tensión en un cable basándose en longitud, sección y material. | `Technical Tool` |

---

## 📈 Hitos de Aprendizaje
1.  **Interoperabilidad:** Estandarización de rutas de archivos para asegurar que el código pueda ser abierto desde cualquier entorno (Windows/WSL2).
2.  **Lógica Industrial:** Implementación de márgenes de seguridad y validación de datos de sensores mediante estructuras condicionales.
3.  **Modularización:** Creación de herramientas reutilizables mediante funciones, optimizando el cálculo de parámetros eléctricos y mecánicos.
4.  **Hito de Ingeniería:** Desarrollo de una calculadora técnica profesional que integra la experiencia en el sector eléctrico con la programación en Python.

---
*Este módulo es parte de mi planificación de 6 meses para especialización en Data Engineer. ¡Siguiente paso: Estructuras de Datos!* 🚀