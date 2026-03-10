warehouse_stock = [
    "item:Interruptor_Magnetotermico;qty:50;price:15.50",
    "item:Cable_Cobre_10mm;qty:100;price:2.20",
    "item:Interruptor_Magnetotermico;qty:20;price:14.00",
    "item:Contactor_Trifasico;qty:0;price:45.00",
    "item:Cable_Cobre_10mm;qty:50;price:-1.00",
    "item:Sensor_Proximidad;qty:10;price:25.00"
]

final_inventory = {}

for line in warehouse_stock:
    # 1. Parsing: Convertimos el string en un diccionario temporal
    # Dividimos por ';' y luego cada parte por ':'
    data = {}
    for part in line.split(';'):
        key, value = part.split(':')
        data[key] = value

    # 2. Conversión de tipos y limpieza
    item_name = data['item']
    qty = int(data['qty'])
    price = float(data['price'])

    # 3. Filtro de Calidad (Regla de negocio)
    if qty <= 0 or price < 0:
        continue  # Saltamos los datos erróneos

    # 4. Consolidación (Agregación)
    if item_name not in final_inventory:
        # Inicializamos el registro si es la primera vez que vemos el item
        final_inventory[item_name] = {
            "total_qty": 0, 
            "total_price_sum": 0.0, 
            "count": 0
        }
    
    # Acumulamos los valores
    final_inventory[item_name]["total_qty"] += qty
    final_inventory[item_name]["total_price_sum"] += price
    final_inventory[item_name]["count"] += 1

# 5. Formateo final: Calculamos el promedio y limpiamos claves temporales
result = {}
for name, stats in final_inventory.items():
    avg = stats["total_price_sum"] / stats["count"]
    result[name] = {
        "total_qty": stats["total_qty"],
        "avg_price": round(avg, 2)
    }

print(result)
        
   


