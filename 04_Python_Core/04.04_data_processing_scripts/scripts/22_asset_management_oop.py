################################################################################
# 22_asset_management_oop.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Gestión de Activos Industriales mediante OOP (Python Core)
#
# ENUNCIADO:
# 1. Crear una clase profesional para la gestión de motores eléctricos.
# 2. Implementar métodos de actualización de estado y cálculo de KPIs técnicos.
# 3. Implementar una subclase VFD_Motor para equipos con variador de frecuencia.
# 4. Foco Técnico: Programación Orientada a Objetos (Clases, Atributos y Métodos).
################################################################################

class ElectricMotor:
    """Clase base para representar un motor eléctrico industrial."""

    def __init__(self, asset_id: str, power_kw: float, runtime_h: float, efficiency: float):
        """
        Inicializa el activo industrial con sus parámetros nominales.
         - asset_id: Identificador único del equipo.
         - power_kw: Potencia nominal en Kilovatios.
         - runtime_h: Horas totales de operación acumuladas.
         - efficiency: Factor de eficiencia (0.0 - 1.0).
        """
        self.asset_id = asset_id
        self.power_kw = power_kw
        self.runtime_h = runtime_h
        self.efficiency = efficiency
        self.energy_consumption = 0.0 # Atributo para almacenar el último cálculo

    def display_technical_specs(self):
        """Muestra por consola la ficha técnica del activo en inglés."""
        print(f'\n' + '='*50)
        print(f'ASSET TECHNICAL DATASHEET')
        print(f'='*50)
        print(f'* ASSET ID: {self.asset_id}')
        print(f'* POWER RATING: {self.power_kw} kW')
        print(f'* TOTAL RUNTIME: {self.runtime_h} h')
        print(f'* EFFICIENCY: {self.efficiency}')

    def update_runtime(self, added_hours: float):
        """Actualiza el contador de horas de funcionamiento."""
        self.runtime_h += added_hours

    def calculate_energy_consumption(self, test_hours: float) -> float:
        """
        Calcula el consumo energético estimado según la potencia y eficiencia.
        Formula: (kW * h) / eficiencia.
        """
        self.energy_consumption = (self.power_kw * test_hours) / self.efficiency
        return self.energy_consumption


class VFDMotor(ElectricMotor):
    """Subclase para motores controlados por Variador de Frecuencia (VFD)."""

    def __init__(self, asset_id: str, power_kw: float, runtime_h: float, efficiency: float, frequency_hz: float):
        """Añade el control de frecuencia a la inicialización del motor base."""
        super().__init__(asset_id, power_kw, runtime_h, efficiency) 
        self.frequency_hz = frequency_hz

    def adjust_frequency(self, new_hz: float):
        """Modifica la frecuencia de trabajo del variador."""
        self.frequency_hz = new_hz

    def display_technical_specs(self):
        """Extiende la ficha técnica para incluir parámetros del variador."""
        super().display_technical_specs()
        print(f'* CURRENT FREQUENCY: {self.frequency_hz} Hz')
        print(f'='*50)


# --- EXECUTION / TEST CASE ---

# Instancia de motor industrial con variador (55kW, 1200h, 0.92 eff, 50Hz)
motor_vfd = VFDMotor('M-02_VFD', 55.0, 1200.0, 0.92, 50.0)

# Simulación de operación
motor_vfd.display_technical_specs()
motor_vfd.update_runtime(150.0)
motor_vfd.adjust_frequency(35.0)
motor_vfd.display_technical_specs()

# Cálculo de KPI de consumo
consumption_kwh = motor_vfd.calculate_energy_consumption(24.0)
print(f'Estimated energy consumption (24h): {consumption_kwh:.2f} kWh')
print(f'='*50)