################################################################################
# 10_customer_hash_map.py
# AUTOR: Aitor | Ingeniero Técnico Industrial | Data Engineer
# PROYECTO: Registro de Clientes con Búsqueda Indexada (Python Core)
#
# ENUNCIADO:
# 1. Crear un sistema de almacenamiento en memoria utilizando Diccionarios.
# 2. Implementar funciones robustas para la inserción (add) y consulta (get)
#    de datos de clientes (ID, Name, Email).
# 3. Aplicar técnicas de Data Wrangling: Normalización (strip, title, lower) 
#    y validación de formatos antes de la carga.
# 4. Foco Técnico: Estructuras Key-Value para búsquedas de alta eficiencia O(1).
################################################################################

customers = {}

def add_customer(customer_id: int, name: str, email: str) -> bool:
    """
    Validates and adds a new customer to the registry.
    Returns True if successful, False otherwise.
    """
    try:
        # Data Normalization
        c_id = int(customer_id)
        c_name = str(name).strip().title() # Title case for professional look
        c_email = str(email).strip().lower()

        # Validation Logic (Guard Clauses)
        if not c_name:
            print("[ERROR] Customer name cannot be empty.")
            return False
            
        if '@' not in c_email:
            print(f"[ERROR] Invalid email format: {c_email}")
            return False

        if c_id in customers:
            print(f"[ERROR] ID {c_id} already exists.")
            return False

        # Insertion
        customers[c_id] = {
            "name": c_name,
            "email": c_email
        }
        print(f"[SUCCESS] Customer {c_id} added.")
        return True

    except (ValueError, TypeError) as e:
        print(f"[ERROR] Critical failure: {e}")
        return False

def get_customer(customer_id: int):
    """Retrieves customer data by ID."""
    return customers.get(customer_id, "[ERROR] Customer not found.")

# --- Testing the implementation ---
add_customer(101, '  aitor  ', 'ait@gmail.com')
add_customer(102, 'John Doe', 'alice@test.com')
add_customer(101, 'Duplicate', 'test@test.com') # Should fail

print("\n--- Current Registry State ---")
print(customers)

print("\n--- Search Test ---")
print(f"Searching ID 101: {get_customer(101)}")
