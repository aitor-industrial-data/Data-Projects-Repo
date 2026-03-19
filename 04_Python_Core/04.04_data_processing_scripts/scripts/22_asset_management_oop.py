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
    def __init__(self, asset_id: str, power_kw: float, runtime_h: float, efficiency: float):
        self.asset_id = asset_id
        self.power_kw = power_kw
        self.runtime_h = runtime_h
        self.efficiency = efficiency  # Eficiencia Nominal (a 50Hz)

    def display_technical_specs(self):
        print(f"[{self.asset_id}] STATUS:")
        print(f" > Power: {self.power_kw} kW")
        print(f" > Runtime: {self.runtime_h} h")
        print(f" > Nom. Efficiency: {self.efficiency:.2f}")

    def update_runtime(self, added_hours: float):
        print(f" >> ACTION: Incrementando runtime en +{added_hours}h")
        self.runtime_h += added_hours

    def calculate_energy_consumption(self, test_hours: float) -> float:
        """Cálculo base usando eficiencia nominal."""
        return (self.power_kw * test_hours) / self.efficiency


class VFDMotor(ElectricMotor):
    def __init__(self, asset_id: str, power_kw: float, runtime_h: float, efficiency: float, frequency_hz: float):
        super().__init__(asset_id, power_kw, runtime_h, efficiency) 
        self.frequency_hz = frequency_hz

    def adjust_frequency(self, new_hz: float):
        print(f" >> ACTION: Ajustando Variador de {self.frequency_hz}Hz a {new_hz}Hz")
        self.frequency_hz = new_hz

    def get_dynamic_efficiency(self):
        """
        LÓGICA DE INGENIERÍA: La eficiencia cae si la frecuencia baja de 50Hz.
        Estimamos una pérdida del 0.5% por cada 5Hz de reducción (Simulación).
        """
        drop_factor = (50 - self.frequency_hz) / 5 * 0.005
        dynamic_eff = self.efficiency - drop_factor
        return max(dynamic_eff, 0.70)  # Límite de seguridad: nunca inferior al 70%

    def calculate_energy_consumption(self, test_hours: float) -> float:
        """Sobrescribe el cálculo usando la eficiencia real según la frecuencia."""
        eff_actual = self.get_dynamic_efficiency()
        print(f" >> INFO: Eficiencia ajustada por frecuencia ({self.frequency_hz}Hz): {eff_actual:.3f}")
        return (self.power_kw * test_hours) / eff_actual

    def display_technical_specs(self):
        eff_actual = self.get_dynamic_efficiency()
        print(f"[{self.asset_id}] CURRENT STATUS:")
        print(f" ├─ Power:      {self.power_kw} kW")
        print(f" ├─ Runtime:    {self.runtime_h} h")
        print(f" ├─ Frequency:  {self.frequency_hz} Hz")
        print(f" └─ Eff_Real:   {eff_actual:.3f}")


# --- EXECUTION ---
print("=" * 65)
print("SISTEMA DE GESTIÓN DE ACTIVOS - CÁLCULO DE EFICIENCIA REAL")
print("=" * 65)

# Motor con eficiencia nominal de 0.92 (92%)
motor_vfd = VFDMotor('M-02_VFD', 55.0, 1200.0, 0.92, 50.0)
motor_vfd.display_technical_specs()

# Reducimos frecuencia a 30Hz (Punto crítico de ventilación)
print("\n[CAMBIO DE PUNTO DE CONSIGNA EN VARIADOR]")
motor_vfd.adjust_frequency(30.0)
motor_vfd.display_technical_specs()

# Comparativa de consumo
print("-" * 65)
consumption = motor_vfd.calculate_energy_consumption(24.0)
print(f"KPI - CONSUMO ESTIMADO (24h) A {motor_vfd.frequency_hz}Hz: {consumption:.2f} kWh")
print("-" * 65)