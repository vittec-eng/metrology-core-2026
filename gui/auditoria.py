#!/usr/bin/env python3
"""
Módulo GUI de Auditoría e Integridad del Sistema Metrología
Contiene la interfaz gráfica para herramientas de auditoría
"""

import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTreeWidgetItem,
    QPushButton, QTreeWidget, QHeaderView, QMessageBox,
    QInputDialog, QApplication, QTreeWidgetItem, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from core.seguridad import verificar_integridad_archivo_vault, generar_y_guardar_hash_vault
from datetime import datetime
from gui.login_dialog import LoginDialog, get_data_path


class VentanaAuditoria(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Auditoría e Integridad del Sistema")
        self.setGeometry(50, 50, 1400, 900)  # Ventana maximizada
        self.setWindowState(Qt.WindowState.WindowMaximized)  # Iniciar maximizada
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Panel superior con Health Check
        health_panel = self.create_health_panel()
        main_layout.addWidget(health_panel)
        
        # Tabla de logs con scroll
        self.create_logs_table()
        main_layout.addWidget(self.logs_table)
        
        # Panel inferior con acciones de recuperación
        recovery_panel = self.create_recovery_panel()
        main_layout.addWidget(recovery_panel)
        
        # Cargar logs al iniciar
        self.cargar_logs()
        QTimer.singleShot(100, self.escanear_sistema)
    
    def create_health_panel(self):
        """Crea el panel de Health Check"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout = QHBoxLayout(panel)
        
        # Botón de escaneo
        self.btn_escanear = QPushButton("🔍 Escanear Sistema")
        self.btn_escanear.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.btn_escanear.clicked.connect(self.escanear_sistema)
        layout.addWidget(self.btn_escanear)
        
        # Etiqueta de estado
        self.health_status = QLabel("⚪ Esperando validación...")
        self.health_status.setStyleSheet("""
            QLabel {
                color: #4ec9b0;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                background-color: #1e1e1e;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.health_status)

        # Etiqueta para la marca de tiempo (ponla en un color gris suave para que no destaque tanto como el estado)
        self.lbl_timestamp = QLabel("Última validación: Pendiente")
        self.lbl_timestamp.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 13px;
                padding-left: 20px;
                font-style: italic;
            }
        """)
        layout.addWidget(self.lbl_timestamp)
        
        layout.addStretch()
        return panel
    
    def create_logs_table(self):
        """Configura el widget de logs como un árbol jerárquico estilo oscuro"""
        from PyQt6.QtWidgets import QTreeWidget, QHeaderView
        
        self.logs_table = QTreeWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHeaderLabels(["Tiempo / Evento", "Tipo", "Usuario", "Descripción"])
        
        # Estilo visual coherente con tu app
        self.logs_table.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                alternate-background-color: #2d2d2d;
                border: 1px solid #3e3e42;
                color: #ffffff;
            }
            QTreeWidget::item {
                padding: 4px;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #ffffff;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #3e3e42;
            }
        """)

        # Configuración de columnas
        header = self.logs_table.header()
        self.logs_table.setColumnWidth(0, 280)
        self.logs_table.setColumnWidth(1, 100)
        self.logs_table.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setRootIsDecorated(True) # Esto habilita la flechita para desplegar
    
    def create_recovery_panel(self):
        """Crea el panel de acciones de recuperación"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout = QHBoxLayout(panel)
        
        # Botón de regeneración de hashes
        self.btn_regenerar = QPushButton("🔧 Regenerar Hashes Corruptos")
        self.btn_regenerar.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:pressed {
                background-color: #ac2925;
            }
        """)
        self.btn_regenerar.clicked.connect(self.regenerar_hashes_corruptos)
        layout.addWidget(self.btn_regenerar)
        
        layout.addStretch()
        return panel
    
    def cargar_logs(self):
        """Carga logs: Colores neutros para evitar fatiga visual"""
        from PyQt6.QtWidgets import QTreeWidgetItem
        from PyQt6.QtGui import QColor, QBrush
        import json
        import os
        
        try:
            ruta_log = "metrologia_log.json"
            if not os.path.exists(ruta_log): return

            with open(ruta_log, 'r', encoding='utf-8') as f:
                sesiones = json.load(f)

            sesiones_ordenadas = list(reversed(sesiones))
            self.logs_table.clear()
            
            for s in sesiones_ordenadas:
                usuario = s.get("user", "Sistema")
                inicio = s.get("start_time", "").replace("T", " ")
                num_sesion = s.get("session_number", "?")
                
                parent = QTreeWidgetItem(self.logs_table)
                parent.setText(0, f"📦 Sesión #{num_sesion} - {inicio}")
                parent.setText(1, "SESIÓN")
                parent.setText(2, usuario)
                
                eventos = s.get("events", [])
                tiene_seguridad = False
                
                for ev in eventos:
                    child = QTreeWidgetItem(parent)
                    hora = ev.get("time", "") 
                    full_action = ev.get("action", "")
                    
                    if ":" in full_action:
                        tipo_ev, desc_ev = full_action.split(":", 1)
                    else:
                        tipo_ev, desc_ev = "INFO", full_action
                    
                    child.setText(0, f"  └─ {hora}")
                    child.setText(1, tipo_ev.strip())
                    child.setText(3, desc_ev.strip())
                    
                    # Colores de texto para los eventos (suaves)
                    desc_lower = desc_ev.lower()
                    if (ev.get("level") == "error" or tipo_ev.strip() == "SECURITY" or 
                        "corrupto" in desc_lower or "incorrecta" in desc_lower):
                        child.setForeground(0, QColor("#ff8585")) # Rojo pastel
                        child.setText(0, "⚠️ " + child.text(0))
                        tiene_seguridad = True
                    elif "re-firmado" in desc_lower:
                        child.setForeground(3, QColor("#a2ffaf")) # Verde pastel
                    elif "hash vault" in desc_lower or "cerrando" in desc_lower:
                        child.setForeground(3, QColor("#4ec9b0")) # Cyan pastel para vault
                        if "cerrando app" in desc_lower:
                            child.setText(0, "🔐 " + child.text(0)) # Icono de cierre de app
                        elif "cerrando sesión" in desc_lower:
                            child.setText(0, "🔒 " + child.text(0)) # Icono de cierre de sesión
                
                # --- PALETA DE COLORES NEUTROS (Descanso visual) ---
                if tiene_seguridad:
                    # Rojo granate muy oscuro y apagado
                    bg_color = QColor("#5a1d1d") 
                else:
                    # Gris azulado neutro (tipo Visual Studio)
                    bg_color = QColor("#37373d") 

                for i in range(4):
                    parent.setBackground(i, bg_color)
                    # Forzamos texto blanco puro para que resalte sin sombras
                    parent.setForeground(i, QColor("#b0b0b0")) 

                parent.setExpanded(False) 

        except Exception as e:
            self.log(f"Error en cargar_logs: {e}")

    def escanear_sistema(self):
        """Escanea todos los JSON y sus hashes para verificar integridad"""
        self.btn_escanear.setEnabled(False)
        self.health_status.setText("🔍 Escaneando sistema...")
        self.health_status.setStyleSheet("""
            QLabel {
                color: #f39c12;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                background-color: #1e1e1e;
                border-radius: 4px;
            }
        """)
        
        QApplication.processEvents()  # Actualizar UI
        
        try:
        # Buscar archivos JSON solo en las subcarpetas de activos reales
            search_roots = []
            for sub_dir in ['patrones', 'instrumentos']:
                ruta = os.path.join('data', sub_dir)
                if os.path.isdir(ruta):
                    search_roots.append(ruta)

            json_files = []
            for root_path in search_roots:
                for root, _, files in os.walk(root_path):
                    for file in files:
                        # Excluimos logs por seguridad, aunque no deberían estar aquí
                        if file.endswith('.json') and not file.endswith('_log.json'):
                            json_files.append(os.path.join(root, file))
            
            corrupt_files = []
            total_files = len(json_files)
            
            self._archivos_corruptos = []
            for i, json_file in enumerate(json_files):
                # Actualizar progreso
                self.health_status.setText(f"🔍 Escaneando {i+1}/{total_files}: {os.path.basename(json_file)}")
                QApplication.processEvents()

                id_elemento = os.path.basename(json_file).replace('.json', '')
                integridad_ok, _ = verificar_integridad_archivo_vault(json_file, id_elemento)
                if not integridad_ok:
                    corrupt_files.append(json_file)
                    self._archivos_corruptos.append(json_file)
            
            # Resultado del escaneo
            if corrupt_files:
                self.health_status.setText(f"⚠️ Se encontraron {len(corrupt_files)} archivos con problemas")
                self.health_status.setStyleSheet("""
                    QLabel {
                        color: #e74c3c;
                        font-weight: bold;
                        font-size: 14px;
                        padding: 10px;
                        background-color: #1e1e1e;
                        border-radius: 4px;
                    }
                """)
                
                # Mostrar detalles
                details = "\n".join([f"• {os.path.basename(f)}" for f in corrupt_files[:10]])
                if len(corrupt_files) > 10:
                    details += f"\n... y {len(corrupt_files)-10} más"
                
                QMessageBox.warning(self, "Archivos corruptos detectados", 
                               f"Se detectaron {len(corrupt_files)} archivos con problemas de integridad:\n\n{details}")
            else:
                self.health_status.setText("✅ Todos los archivos son íntegros")
                self.health_status.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        font-weight: bold;
                        font-size: 14px;
                        padding: 10px;
                        background-color: #1e1e1e;
                        border-radius: 4px;
                    }
                """)
                
        except Exception as e:
            self.health_status.setText(f"❌ Error en escaneo: {str(e)}")
            self.health_status.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 10px;
                    background-color: #1e1e1e;
                    border-radius: 4px;
                }
            """)
        
        finally:
            self.btn_escanear.setEnabled(True)
            ahora = datetime.now().strftime("%H:%M:%S")
            self.lbl_timestamp.setText(f"Última validación: {ahora}")
    
    def regenerar_hashes_corruptos(self):
        """Regenera hashes y registra exactamente qué archivos han sido firmados"""
        from datetime import datetime
        from core.logger import get_logger
            
        logger = get_logger()
        
        # 1. Pedir clave
        password_input, ok = QInputDialog.getText(
            self, "Confirmación Administrativa", 
            "Ingrese su contraseña para autorizar la re-firma:", 
            QLineEdit.EchoMode.Password
        )
        if not ok or not password_input: return
        
        try:
            # 2. Validar Admin
            with open(get_data_path('config/users.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            admin_data = next((u for u in data['tecnicos'] if u['username'].lower() == 'admin'), None)
            login_tool = LoginDialog()
            
            if not admin_data or password_input != login_tool.desencriptar_password(admin_data['password']):
                logger.log_event("SECURITY", "Intento fallido de regeneración: Credenciales inválidas", level="warning")
                QMessageBox.critical(self, "Error", "Acceso denegado.")
                return

            nombre_admin = admin_data.get('username', 'admin')

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de validación: {e}")
            return

        # 3. Regeneración con captura de IDs
        try:
            if not hasattr(self, '_archivos_corruptos'):
                self.escanear_sistema()

            archivos_objetivo = list(getattr(self, '_archivos_corruptos', []))
            if not archivos_objetivo:
                QMessageBox.information(self, "Sin cambios", "No hay archivos corruptos.")
                return

            regenerated = 0
            nombres_reparados = [] # <--- Lista para guardar los nombres

            for json_file in archivos_objetivo:
                # Extraer el ID (ej: ME-0001)
                id_elemento = os.path.basename(json_file).replace('.json', '')
                
                if generar_y_guardar_hash_vault(json_file, id_elemento):
                    regenerated += 1
                    nombres_reparados.append(id_elemento) # <--- Guardamos el ID
            
            # 4. Registro detallado en el Log
            if regenerated > 0:
                lista_str = ", ".join(nombres_reparados) # Unimos los nombres por comas
                detalle_accion = f"Re-firmados {regenerated} archivos: [{lista_str}]"
                
                # Usamos el método de registro administrativo
                if hasattr(logger, 'registrar_accion_administrativa'):
                    logger.registrar_accion_administrativa(nombre_admin, "REGENERACIÓN_HASHES", detalle_accion)
                else:
                    logger.log_event("DATA", f"ADMIN[{nombre_admin}]: {detalle_accion}", level="success")

            # 5. UI
            ahora = datetime.now().strftime("%H:%M:%S")
            self.lbl_timestamp.setText(f"Última validación: {ahora} (Firma: {nombre_admin})")
            
            QMessageBox.information(self, "Éxito", f"Se han re-firmado: {', '.join(nombres_reparados)}")
            
            self.cargar_logs()
            self._archivos_corruptos = [] 
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo en proceso: {str(e)}")