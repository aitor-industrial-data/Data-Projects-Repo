################################################################################
# 17_list_to_txt_export.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Generador de Auditoría Energética de Motores (Python Core)
#
# ENUNCIADO:
# 1. Definir una estructura de datos basada en diccionarios para flota industrial.
# 2. Implementar funciones de cálculo de consumo (kWh) y diagnóstico de uso.
# 3. Exportar los resultados procesados a un archivo físico .txt plano.
# 4. Foco Técnico: Persistencia de datos, formateo de strings y gestión de I/O.
################################################################################

from datetime import datetime

# 1. Definimos las funciones lógicas de forma independiente
def calculate_consumption(power_kw, efficiency, runtime_h):
    """Calcula la energía consumida basándose en la eficiencia."""
    return (power_kw / efficiency) * runtime_h

def get_status(runtime_h):
    """Determina el estado según las horas de uso."""
    return 'High Usage' if runtime_h > 5000 else 'Normal'

# 2. Datos representados como una lista de diccionarios (Data Engineering style)
motor_fleet = [
    {'asset_id': 'M-02_VFD', 'power_kw': 55.0, 'runtime_h': 1200.0, 'efficiency': 0.92},
    {'asset_id': 'M-03', 'power_kw': 145.0, 'runtime_h': 1500.0, 'efficiency': 0.72},
    {'asset_id': 'V-02_V', 'power_kw': 100.0, 'runtime_h': 1250.0, 'efficiency': 0.92},
    {'asset_id': 'M-01', 'power_kw': 30.5, 'runtime_h': 5090.0, 'efficiency': 0.98}
]

def export_to_txt(fleet, filename):
    with open(filename, "w", encoding="utf-8") as file:
        # Encabezado del reporte
        file.write('\n' + '='*115)
        file.write('\nINDUSTRIAL MOTOR AUDIT REPORT')
        file.write(f'\nDate: {datetime.now().date()}')
        file.write('\n' + '='*115)
        
        # Cabecera de columnas alineada
        header = f'\n{"ID":<20}{"POWER(kW)":<20}{"HOURS":<20}{"EFFICIENCY":<20}{"CONSUMPTION(kWh)":<20}{"STATUS"}'
        file.write(header)
        file.write('\n' + '-'*115)

        total_consumption = 0
        
        # 3. Procesamiento y escritura de cada registro
        for motor in fleet:
            consumption = calculate_consumption(
                motor['power_kw'], 
                motor['efficiency'], 
                motor['runtime_h']
            )
            status = get_status(motor['runtime_h'])
            
            line = (f"\n{motor['asset_id']:<20}"
                    f"{motor['power_kw']:<20}"
                    f"{motor['runtime_h']:<20}"
                    f"{motor['efficiency']:<20}"
                    f"{consumption:<20.2f}"
                    f"{status}")
            
            file.write(line)
            total_consumption += consumption

        # Pie de página con totales
        file.write('\n' + '-'*115)
        file.write(f'\nTOTAL FLEET CONSUMPTION: {total_consumption:.2f} kWh')
        file.write('\n' + '='*115)

# Ejecución del proceso
if __name__ == "__main__":
    export_to_txt(motor_fleet, 'motor_audit_report.txt')
    print(f"Report successfully generated as 'motor_audit_report.txt'")