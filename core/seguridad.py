import hashlib
import os
import json


def generar_hash_archivo(ruta_archivo):
    SAL_SECRETA = b"METROLOGIA_2024_HASH_SALT_SECURE"
    hash_sha256 = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        contenido = f.read()
        hash_sha256.update(contenido + SAL_SECRETA)
    return hash_sha256.hexdigest()


def generar_y_guardar_hash(ruta_json, id_elemento):
    try:
        hash_valor = generar_hash_archivo(ruta_json)
        ruta_hash = ruta_json.replace('.json', '.hash')
        with open(ruta_hash, 'w', encoding='utf-8') as f:
            f.write(hash_valor)
        return True
    except Exception:
        return False


def verificar_integridad_archivo(ruta_json, id_elemento):
    ruta_hash = ruta_json.replace('.json', '.hash')

    if not os.path.exists(ruta_hash):
        return False, "No existe archivo de referencia (hash) - posible manipulación"

    try:
        with open(ruta_hash, 'r', encoding='utf-8') as f:
            hash_guardado = f.read().strip()
    except Exception:
        return False, "Error leyendo archivo hash"

    try:
        hash_actual = generar_hash_archivo(ruta_json)
    except Exception:
        return False, "Error generando hash del archivo JSON"

    if hash_actual == hash_guardado:
        return True, "Integridad verificada"

    return False, "Discrepancia detectada: el archivo ha sido modificado"


# === NUEVAS FUNCIONES PARA VAULT DE HASHES ===

def sellar_log_sistema():
    """Esta función se llama SIEMPRE al cerrar, sea quien sea el usuario"""
    try:
        ruta_log = 'metrologia_log.json'
        ruta_hash_log = 'metrologia_log.hash'
        
        if os.path.exists(ruta_log):
            # Generamos el hash del estado actual del log (con las acciones del visor)
            nuevo_hash = generar_hash_archivo(ruta_log)
            with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                f.write(nuevo_hash)
            return True
    except Exception as e:
        self.log(f"Error sellando log: {e}")
    return False

def obtener_ruta_vault():
    """Retorna la ruta del vault de hashes"""
    return "hashes_vault.json"


def cargar_vault_hashes():
    """Carga el vault de hashes desde archivo con manejo robusto de errores"""
    ruta_vault = obtener_ruta_vault()
    if os.path.exists(ruta_vault):
        try:
            with open(ruta_vault, 'r', encoding='utf-8') as f:
                vault_data = json.load(f)
                
            # Verificar que sea un diccionario válido
            if not isinstance(vault_data, dict):
                return {}
                
            # Verificar que los hashes sean válidos
            vault_valido = {}
            for key, value in vault_data.items():
                if isinstance(value, str) and len(value) == 64:
                    vault_valido[key] = value
                    
            return vault_valido
            
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            return {}
    else:
        return {}


def guardar_vault_hashes(vault_data):
    """Guarda el vault de hashes a archivo con orden consistente"""
    ruta_vault = obtener_ruta_vault()
    try:
        # Ordenar alfabéticamente para consistencia
        if isinstance(vault_data, dict):
            # Filtrar elementos válidos (solo hashes simples de 64 caracteres)
            vault_ordenado = {}
            for key in sorted(vault_data.keys()):
                value = vault_data[key]
                # Solo incluir si es un hash simple (SHA256 = 64 chars)
                if isinstance(value, str) and len(value) == 64:
                    vault_ordenado[key] = value
                # Excluir explícitamente session_counter y otros elementos no-hash
                elif key == 'session_counter':
                    continue  # Ignorar session_counter - se maneja por separado
                else:
                    continue  # Ignorar otros elementos que no sean hashes simples
            vault_data = vault_ordenado
        
        with open(ruta_vault, 'w', encoding='utf-8') as f:
            json.dump(vault_data, f, indent=2, ensure_ascii=False, sort_keys=True)
        return True
    except Exception:
        return False


def generar_y_guardar_hash_vault(ruta_json, id_elemento):
    """Genera hash y lo guarda en el vault centralizado"""
    # Esta función ahora solo se usa para archivos individuales, no para el vault principal
    try:
        hash_valor = generar_hash_archivo(ruta_json)
        vault = cargar_vault_hashes()
        vault[id_elemento] = hash_valor
        return guardar_vault_hashes(vault)
    except Exception:
        return False


def generar_vault_completo():
    """Genera el vault completo recorriendo todos los JSON y devuelve su hash"""
    import time
    
    try:
        # 1. Recorrer todos los JSON actuales y generar hashes
        vault = {}
        carpetas_permitidas = ['data/patrones', 'data/instrumentos']
        
        for carpeta in carpetas_permitidas:
            if not os.path.exists(carpeta):
                continue
                
            for root, _, files in os.walk(carpeta):
                for file in files:
                    if file.endswith('.json'):
                        ruta_json = os.path.join(root, file)
                        id_elemento = file.replace('.json', '')
                        
                        try:
                            hash_valor = generar_hash_archivo(ruta_json)
                            vault[id_elemento] = hash_valor
                        except Exception:
                            continue
        
        # 2. Guardar el vault completo con sincronización forzada
        if guardar_vault_hashes(vault):
            # Forzar sincronización de escritura
            ruta_vault = obtener_ruta_vault()
            with open(ruta_vault, 'r+b') as f:
                f.flush()
                os.fsync(f.fileno())
            
            # Pequeña pausa para asegurar escritura completa
            time.sleep(0.1)
            
            # 3. Generar hash del archivo vault y retornarlo
            hash_vault = generar_hash_archivo(ruta_vault)
            return hash_vault, len(vault)
        else:
            return None, 0
            
    except Exception:
        return None, 0


def verificar_integridad_archivo_vault(ruta_json, id_elemento):
    """Verifica integridad usando el vault de hashes"""
    vault = cargar_vault_hashes()
    
    if id_elemento not in vault:
        return False, "No existe hash en vault para este elemento"

    hash_guardado = vault[id_elemento]
    
    try:
        hash_actual = generar_hash_archivo(ruta_json)
    except Exception:
        return False, "Error generando hash del archivo JSON"

    if hash_actual == hash_guardado:
        return True, "Integridad verificada desde vault"

    return False, f"Discrepancia detectada: el archivo {id_elemento} ha sido modificado"


def migrar_hashes_a_vault():
    """Migra todos los archivos .hash individuales al vault centralizado"""
    vault = {}
    migrados = 0
    
    # Buscar SOLO en data/patrones y data/instrumentos
    carpetas_permitidas = ['data/patrones', 'data/instrumentos']
    
    for carpeta in carpetas_permitidas:
        if not os.path.exists(carpeta):
            continue
            
        for root, _, files in os.walk(carpeta):
            for file in files:
                if file.endswith('.json'):  # Buscar archivos JSON, no .hash
                    ruta_json = os.path.join(root, file)
                    # Generar ID del elemento desde el nombre del archivo
                    id_elemento = file.replace('.json', '')
                    
                    try:
                        # Generar hash del archivo JSON
                        hash_valor = generar_hash_archivo(ruta_json)
                        vault[id_elemento] = hash_valor
                        migrados += 1
                    except Exception:
                        continue
    
    # Guardar vault
    if guardar_vault_hashes(vault):
        return migrados
    return 0


# === FUNCIONES PARA SESSION_COUNTER (separado del vault) ===

def verificar_session_counter():
    """Verifica la integridad del session_counter por separado"""
    from core.session_manager import leer_numero_sesion
    
    try:
        session_number, is_valid = leer_numero_sesion()
        if session_number is None:
            return False, "No existe archivo session_counter"
        
        if not is_valid:
            return False, f"Session_counter manipulado (sesión: {session_number})"
        
        return True, f"Session_counter válido (sesión: {session_number})"
    except Exception as e:
        return False, f"Error verificando session_counter: {str(e)}"


def generar_hash_vault():
    """Genera hash del vault completo para registro de integridad"""
    try:
        ruta_vault = obtener_ruta_vault()
        if os.path.exists(ruta_vault):
            return generar_hash_archivo(ruta_vault)
        return None
    except Exception:
        return None


def obtener_ultimo_hash_vault_del_log():
    """Extrae el último hash del vault guardado en el log"""
    try:
        ruta_log = 'metrologia_log.json'
        if not os.path.exists(ruta_log):
            return None
            
        with open(ruta_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Buscar el último registro de hash del vault
        for sesion in reversed(log_data):
            for evento in reversed(sesion.get('events', [])):
                action = evento.get('action', '')
                if 'Hash vault:' in action:
                    hash_part = action.split('Hash vault:')[1].split()[0]
                    return hash_part
        return None
    except Exception:
        return None
