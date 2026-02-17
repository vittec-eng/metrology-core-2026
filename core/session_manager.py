import json
import os
import hashlib
from datetime import datetime

# Configuración
SALT_SESION = "METROLOGIA_2024_SESSION_SALT_SECURE"
SESSION_FILE = "data/session_counter.hash"

# Variable global para controlar incrementos múltiples
_ya_picamos_windsurf = False

# Variable global para evitar incrementos múltiples
_ya_incrementada_sesion = False

def generar_hash_sesion(session_number):
    """Genera hash SHA-256 con sal para el número de sesión"""
    hash_obj = hashlib.sha256()
    hash_obj.update(f"{session_number}{SALT_SESION}".encode('utf-8'))
    return hash_obj.hexdigest()

def guardar_numero_sesion(session_number):
    """Guarda el número de sesión con su hash"""
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        session_hash = generar_hash_sesion(session_number)
        
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'session_number': session_number,
                'session_hash': session_hash,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        return True
    except Exception as e:
        self.log(f"Error guardando número de sesión: {e}")
        return False

def leer_numero_sesion():
    """Lee y verifica el número de sesión desde el archivo"""
    try:
        if not os.path.exists(SESSION_FILE):
            return None, None
        
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stored_number = data.get('session_number')
        stored_hash = data.get('session_hash')
        
        # Verificar integridad del hash
        calculated_hash = generar_hash_sesion(stored_number)
        
        if calculated_hash == stored_hash:
            return stored_number, True  # Válido
        else:
            return stored_number, False  # Manipulado
            
    except Exception as e:
        self.log(f"Error leyendo número de sesión: {e}")
        return None, None

def reset_flag_incremento():
    """Resetea el flag de incremento para允许 incrementos en nuevas instancias"""
    global _ya_incrementada_sesion
    _ya_incrementada_sesion = False

def incrementar_sesion():
    """Incrementa el número de sesión y lo guarda"""
    global _ya_incrementada_sesion
    
    try:
        if _ya_incrementada_sesion:
            return None
        
        _ya_incrementada_sesion = True
        current_number, _ = leer_numero_sesion()
        if current_number is None:
            current_number = 0
        
        new_number = current_number + 1
        if guardar_numero_sesion(new_number):
            return new_number
        else:
            return None
    except Exception as e:
        self.log(f'Error incrementando sesión: {e}')
        return None

def restaurar_numero_sesion(session_number):
    """Restaura el número de sesión (solo para administrador)"""
    return guardar_numero_sesion(session_number)

if __name__ == "__main__":
    # Prueba del sistema
    # print("=== Sistema de Gestión de Sesiones ===")
    
    # Incrementar sesión
    new_session = incrementar_sesion()
    # print(f"Nueva sesión: {new_session}")
    
    # Leer y verificar
    number, valid = leer_numero_sesion()
    # print(f"Sesión leída: {number}, Válida: {valid}")
