################################################################################
# 12_sql_style_filtering.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Análisis de Costes mediante List Comprehensions (Python Core)
#
# ENUNCIADO:
# 1. Identificar precios de mercado anómalos superiores a la media.
# 2. Implementar lógica de filtrado SQL-style en una sola línea.
# 3. Generar un reporte de desviaciones para negociación de costes.
# 4. Foco Técnico: List Comprehensions, Tuplas y Librería Statistics.
################################################################################

import statistics as stats

# 1. Dataset Inicial (Raw Data)
market_prices = [120.50, 89.99, 340.25, 45.10, 560.00, 110.00, 230.75]

# 2. Cálculo de Referencia (Benchmark)
price_threshold = round(stats.mean(market_prices), 2)

# 3. List Comprehension (Core del Ejercicio)
# Generamos registros categorizados para precios por encima del umbral
high_cost_records = [(price, 'ABOVE_AVG') for price in market_prices if price > price_threshold]

# 4. Cálculo de Desviaciones (Cost Deltas)
# Diferencia exacta respecto a la media para cada registro detectado
cost_deltas = [round(record[0] - price_threshold, 2) for record in high_cost_records]

# 5. Reporte de Inteligencia de Negocio
print("="*45)
print(f"ANÁLISIS DE COSTES OPERATIVOS | Media: {price_threshold}€")
print("="*45)

# Combinamos los resultados para una lectura clara
for record, delta in zip(high_cost_records, cost_deltas):
    print(f"Precio: {record[0]:>7}€ | Estado: {record[1]} | Delta: +{delta:>6}€")

print("-" * 45)
total_overcost = round(sum(cost_deltas), 2)
print(f"IMPACTO TOTAL EN SOBRECOSTE: {total_overcost}€")
print("=" * 45)