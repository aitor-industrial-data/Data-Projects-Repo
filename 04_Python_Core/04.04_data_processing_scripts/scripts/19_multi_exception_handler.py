################################################################################
# 19_multi_exception_handler.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Diagnóstico de Fallos en Cálculos de Eficiencia Energética
#
# ENUNCIADO:
# 1. Desarrollar una función de cálculo de consumo que detecte múltiples errores.
# 2. Gestionar específicamente el error de división por cero (ZeroDivisionError).
# 3. Capturar errores de tipo de dato (ValueError) en la entrada de parámetros.
# 4. Implementar un bloque "finally" para asegurar el cierre de logs de auditoría.
# 5. Foco Técnico: Jerarquía de Excepciones, Gestión de Errores Específicos y Trazabilidad.
################################################################################

from datetime import datetime
import logging

# CONFIGURACIÓN DEL LOGGER
# format: Fecha/Hora - Nivel de importancia - Mensaje
logging.basicConfig(
    filename='motor_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def safe_energy_calculation(asset_id: str, power: float, efficiency: float, hours: float):
    try:
        # Forzamos la conversión aquí para capturar el ValueError si vienen como strings numéricos
        p = float(power)
        e = float(efficiency)
        h = float(hours)
        
        energy = (p * h) / e
        print(f"Result: {energy:.2f} kWh")
        return energy

    except ZeroDivisionError:
        print(f'[CRITICAL] Efficiency cannot be zero. Physics laws violation.')
    except ValueError as ve:
        print(f'[ERROR] Invalid numeric value: {ve}')
    except TypeError as te:
        print(f'[ERROR] Incompatible data types: {te}')
    except Exception as e:
        print(f'Error no contemplado: {e}. Se recomienda despido inminente ;)')
    finally:
     # Esto siempre se registra para saber que el proceso terminó
        logging.info(f"Process attempt for {asset_id} finished.")


# Pruebas de estrés
safe_energy_calculation('M01', 50, 0.85, 100)               # OK
safe_energy_calculation('motor2.3', 50, 0, 100)             # ZeroDivision
safe_energy_calculation('2345', 'cincuenta', 0.85, 100)     # ValueError (al hacer float())
safe_energy_calculation('M01', 50, 0.85, None)              # TypeError

print("\nProceso finalizado. Revisa el archivo 'motor_audit.log' para ver los resultados.")