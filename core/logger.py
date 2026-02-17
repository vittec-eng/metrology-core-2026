"""
Sistema de logging centralizado para la aplicación de metrología.
Registra sesiones, navegaciones, calibraciones y eventos del sistema.
"""

import os
import json
import sys
from datetime import datetime

# Importar gestor de sesiones
from .session_manager import incrementar_sesion, leer_numero_sesion, generar_hash_sesion


class SessionLogger:
    """Logger centralizado para tracking de sesiones y eventos"""
    
    def __init__(self, log_file="metrologia_log.json"):
        self.log_file = log_file
        
        # NO incrementar sesión todavía - solo leer el número actual
        self.session_number = None  # Se establecerá cuando el usuario inicie sesión
        self.session_incremented = False
        
        self.start_time = datetime.now()
        self.user = None
        self.events = []
        self.session_created = False
        self._init_log_file()
    
    def _init_log_file(self):
        """Inicializa o carga el archivo de log"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            
            # Guardar evento de creación inicial como SECURITY
            initial_event = {
                "session_number": "CREACION_INICIAL",
                "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "user": "SYSTEM",
                "events": [
                    {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "action": "SECURITY: Sistema inicializado - Archivo de log creado"
                    }
                ]
            }
            
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump([initial_event], f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.log(f"Error guardando evento inicial: {e}")
    
    def incrementar_numero_sesion_si_es_necesario(self):
        """Incrementa el número de sesión solo si no se ha hecho antes"""
        if not self.session_incremented:
            self.session_number = incrementar_sesion()
            if self.session_number is None:
                self.session_number = 0
            self.session_incremented = True
            return True
        return False
    
    def _create_session(self):
        """Crea la entrada de la sesión en el log con todos los datos"""
        # Si no hay número de sesión, es una acción administrativa
        if self.session_number is None:
            session_number = f"ADMIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            session_number = self.session_number
            
        session_data = {
            "session_number": session_number,
            "start_time": self.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "user": self.user,
            "events": []
        }
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            logs.append(session_data)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            self.session_created = True
        except Exception as e:
            self.log(f"Error creando sesión: {e}")
    
    def set_user(self, username):
        """Registra el usuario actual y crea la sesión solo si no es una acción administrativa"""
        self.user = username
        
        # Incrementar número de sesión solo si no se ha hecho antes
        if not self.session_created:
            # Actualizar start_time justo cuando el usuario inicia sesión
            self.start_time = datetime.now()
            self.incrementar_numero_sesion_si_es_necesario()
            self._create_session()
        self.log_event("SYSTEM", f"App iniciada")
    
    def registrar_accion_administrativa(self, username, accion, detalle=""):
        """Registra una acción administrativa sin incrementar número de sesión"""
        self.user = username
        
        # NO incrementar número de sesión para acciones administrativas
        if not self.session_created:
            self._create_session()
        
        self.log_event("SECURITY", f"Acción administrativa: {accion}")
        if detalle:
            self.log_event("SECURITY", f"Detalle: {detalle}")
    
    def log_event(self, event_type, message, level="info"):
        """
        Registra un evento en la sesión actual
        
        Args:
            event_type: Tipo de evento (SYSTEM, NAV, DATA, AUTH, ERROR, etc.)
            message: Mensaje descriptivo
            level: Nivel del evento (info, warning, error, success)
        """
        # Solo registrar eventos si la sesión ya fue creada
        if not self.session_created:
            return
            
        event_time = datetime.now().strftime("%H:%M:%S")
        event = {"time": event_time, "action": f"{event_type}: {message}"}
        
        self.events.append(event)
        self._append_event_to_file(event)
    
    def log_security_event(self, event_type, message, level="warning"):
        """
        Registra un evento de seguridad que no requiere sesión de usuario
        
        Args:
            event_type: Tipo de evento (SECURITY)
            message: Mensaje descriptivo
            level: Nivel del evento (warning, error)
        """
        # Asegurar que el archivo de log exista
        self._init_log_file()
        
        # Forzar creación de sesión administrativa si no existe
        if not self.session_created:
            self.user = "SYSTEM"
            self._create_session()
            
        event_time = datetime.now().strftime("%H:%M:%S")
        event = {"time": event_time, "action": f"{event_type}: {message}"}
        
        self.events.append(event)
        self._append_event_to_file(event)
    
    def log_navigation(self, from_page, to_page, user=None):
        """Registra navegación entre páginas"""
        message = f"Acceso a {from_page} → {to_page}"
        self.log_event("NAV", message)
    
    def log_calibration(self, elemento_id, familia, usuario, numero_informe=None):
        """Registra una calibración realizada"""
        message = f"Calibración: {elemento_id} ({familia})"
        if numero_informe:
            message += f" - Informe: {numero_informe}"
        self.log_event("DATA", message)
    
    def log_file_upload(self, filename, elemento_id, file_type):
        """Registra la carga de archivos"""
        message = f"Archivo: {filename} ({file_type}) para {elemento_id}"
        self.log_event("DATA", message)
    
    def log_error(self, error_type, error_message):
        """Registra errores del sistema"""
        message = f"[{error_type}] {error_message}"
        self.log_event("ERROR", message)
    
    def log_element_creation(self, elemento_id, familia):
        """Registra creación de elementos"""
        message = f"Creado: {elemento_id} en {familia}"
        self.log_event("DATA", message)

    def log_status_change(self, elemento_id, nuevo_estado, usuario):
        """Registra el cambio de estado de un instrumento"""
        message = f"{elemento_id} marcado como {nuevo_estado.upper()} por {usuario}"
        self.log_event("DATA", message)
    
    def _append_event_to_file(self, event):
        """Agrega un evento a la sesión actual en el archivo"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Buscar la sesión actual (la última)
            if logs:
                logs[-1]["events"].append(event)
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.log(f"Error escribiendo evento: {e}")
    
    def log_hash_vault(self, hash_vault, total_hashes, evento_tipo="APP"):
        """
        Registra el hash del vault de forma forzada (independiente de sesión)
        
        Args:
            hash_vault: Hash generado del vault
            total_hashes: Total de elementos en el vault
            evento_tipo: "APP" para cierre de app, "SESION" para cierre de sesión
        """
        try:
            # Forzar creación de sesión solo si no existe ninguna
            if not self.session_created:
                self._create_session()
            
            event_time = datetime.now().strftime("%H:%M:%S")
            if evento_tipo == "APP":
                message = f"[CERRANDO APP] Hash vault: {hash_vault[:16]}... (total: {total_hashes} elementos)"
            else:
                message = f"[CERRANDO SESIÓN] Hash vault: {hash_vault[:16]}... (total: {total_hashes} elementos)"
            
            # Usar el método estándar log_event para evitar duplicación
            self.log_event("SYSTEM", message)
        
        except Exception as e:
            self.log(f"Error registrando hash vault: {e}")

    def end_session(self):
        """Finaliza la sesión actual"""
        end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Actualizar la sesión actual (la última)
            if logs:
                logs[-1]["end_time"] = end_time
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.log(f"Error finalizando sesión: {e}")


# Instancia global del logger
_global_logger = None


def get_logger():
    """Obtiene la instancia global del logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = SessionLogger()
    return _global_logger


def init_logger():
    """Inicializa el logger global"""
    global _global_logger
    _global_logger = SessionLogger()
    return _global_logger
