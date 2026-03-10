almacen_norte = ["CABLE-100", "ENCHUFE-50", "CABLE-200", "MAGNETO-15"]
almacen_sur = ["cable:50", "magneto:10", "enchufe:10", "tubo:100"]

inventario_total = []
nombres_vistos = [] # Tu "lista" para control de duplicados

# PROCESAR NORTE
for item in almacen_norte:
    nombre, cantidad = item.lower().split('-')
    cantidad = int(cantidad) # Convertir a número
    
    # Si quieres sumar cantidades de elementos repetidos (como CABLE):
    if nombre not in nombres_vistos:
        inventario_total.append([nombre, cantidad])
        nombres_vistos.append(nombre)
    else:
        # Si ya existe, buscamos el índice y sumamos la cantidad
        for sublista in inventario_total:
            if sublista[0] == nombre:
                sublista[1] += cantidad

# PROCESAR SUR
for item in almacen_sur:
    nombre, cantidad = item.lower().split(':') # ¡Aquí usamos dos puntos!
    cantidad = int(cantidad)
    
    if nombre not in nombres_vistos:
        inventario_total.append([nombre, cantidad])
        nombres_vistos.append(nombre)
    else:
        for sublista in inventario_total:
            if sublista[0] == nombre:
                sublista[1] += cantidad

print("Inventario Consolidado:")
print(inventario_total)

# Cálculo del total global
total_piezas = sum(item[1] for item in inventario_total)
print(f"\nSuma total de piezas: {total_piezas}")