################################################################################
# 09_inventory_list_manager.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Gestión de Stock y Auditoría de Almacén Eléctrico (Python Core)
#
# OBJETIVOS:
# 1. Identificar componentes faltantes (En sistema pero no en estantería).
# 2. Detectar "intrusos" (Material físico no registrado en el sistema).
# 3. Calcular discrepancias de unidades entre stock teórico y real.
# 4. Alertar sobre falta de componentes críticos (Categoría "A").
# 5. Foco Técnico: Operaciones CRUD sobre listas y lógica de conciliación.
################################################################################

# --- ENTRADA DE DATOS (INPUTS) ---
# [ID_Componente, Categoría, Cantidad_Teórica]
stock_sistema = [
    ["INV-001", "A", 50],  # Categoría A: Crítico (ej. Autómatas)
    ["INV-002", "C", 100], # Categoría C: Consumible (ej. Bornas)
    ["INV-003", "B", 25],  # Categoría B: Importante (ej. Magnetotérmicos)
    ["INV-004", "A", 10],
    ["INV-005", "C", 200]
]

# [ID_Componente, Ubicación, Cantidad_Física]
auditoria_fisica = [
    ["INV-001", "Pasillo 1", 48],
    ["INV-003", "Pasillo 2", 25],
    ["INV-005", "Pasillo 1", 190],
    ["INV-006", "Pasillo 3", 5]   # Componente nuevo/intruso encontrado físicamente
]

# --- PRE-PROCESAMIENTO ---
# Extraemos los IDs para facilitar la comparación cruzada
ids_sistema = [comp[0] for comp in stock_sistema]
ids_fisicos = [aud[0] for aud in auditoria_fisica]

# --- 1. IDENTIFICACIÓN DE COMPONENTES FALTANTES E INTRUSOS ---
# Están en el sistema, pero no se encontraron en la auditoría física
componentes_faltantes = [cid for cid in ids_sistema if cid not in ids_fisicos]
# Están en la estantería, pero no figuraban en el inventario del sistema
componentes_no_registrados = [cid for cid in ids_fisicos if cid not in ids_sistema]

print(f"Componentes Faltantes (Sin rastro físico): {componentes_faltantes}")
print(f"Componentes Intrusos (No registrados en sistema): {componentes_no_registrados}")

# --- 2. ANÁLISIS DE DISCREPANCIAS Y ALERTAS DE CRITICIDAD ---
alertas_criticas_stock = 0

print("\n" + "="*50)
print("     INFORME DE DISCREPANCIAS DE INVENTARIO")
print("="*50)

for comp in stock_sistema:
    id_comp = comp[0]
    categoria = comp[1]
    qty_teorica = comp[2]

    # Comprobamos si el componente se encontró en la auditoría
    if id_comp in ids_fisicos:
        # Buscamos el registro físico para comparar cantidades
        for aud in auditoria_fisica:
            if aud[0] == id_comp:
                qty_fisica = aud[2]
                discrepancia = qty_fisica - qty_teorica
                
                # Solo imprimimos si hay diferencia
                if discrepancia != 0:
                    estado = "EXCESO" if discrepancia > 0 else "FALTA"
                    print(f"{id_comp}: Sistema {qty_teorica} | Físico {qty_fisica} | Dif: {discrepancia} ({estado})")
                else:
                    print(f"{id_comp}: Stock verificado (OK)")
    else:
        # Lógica de Negocio: Alertar si falta un componente de categoría crítica "A"
        if categoria == "A":
            alertas_criticas_stock += 1

print("="*50)
print(f"ALERTA DE ALMACÉN: {alertas_criticas_stock} componentes CRÍTICOS (Cat. A) están totalmente agotados.")