import sys
import os
import json
import hashlib
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QDockWidget, QTreeView, QInputDialog, QFileDialog, QPushButton, QScrollArea, QFrame, QGridLayout, QLabel, QTextEdit, QMessageBox, QDialog, QHeaderView, QHBoxLayout, QStackedWidget, QGraphicsBlurEffect, QTableWidget, QTableWidgetItem, QComboBox, QTabWidget, QButtonGroup
from PyQt6.QtGui import QFileSystemModel, QColor
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from gui.styles import STYLE_SHEET
from gui.login_dialog import LoginDialog
from gui.gestion_usuarios import GestionUsuariosDialog
from gui.element_window import ElementWindow
from fpdf import FPDF
from core.pdf_generator import exportar_a_pdf
from core.logger import init_logger, get_logger
from core.seguridad import generar_hash_archivo, generar_y_guardar_hash_vault, verificar_integridad_archivo_vault, cargar_vault_hashes, obtener_ruta_vault, verificar_session_counter, generar_vault_completo
from gui.auditoria import VentanaAuditoria
import qtawesome as qta
from PyQt6.QtWidgets import QFileIconProvider
import statistics
import shutil

def actualizar_hash_vault_en_log(hash_vault_actual, logger=None):
    """Actualiza el último registro de hash del vault en el log"""
    try:
        ruta_log = 'metrologia_log.json'
        with open(ruta_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # Buscar la última sesión y actualizar su hash del vault
        if log_data:
            ultima_sesion = log_data[-1]
            eventos = ultima_sesion.get('events', [])
            
            # Buscar si ya existe un registro de hash del vault
            for i, evento in enumerate(reversed(eventos)):
                action = evento.get('action', '')
                if 'Hash vault:' in action:
                    # Actualizar el hash del vault en el registro existente
                    vault = cargar_vault_hashes()
                    total_elementos = len(vault)
                    eventos[len(eventos) - 1 - i]['action'] = f"SYSTEM: [CERRANDO SESIÓN] Hash vault: {hash_vault_actual[:16]}... (total: {total_elementos} elementos)"
                    
                    # Guardar el log actualizado
                    with open(ruta_log, 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, indent=2, ensure_ascii=False)
                    
                    if logger:
                        logger.log(f'[SYNC] Hash del vault actualizado en log: {hash_vault_actual[:16]}...')
                    else:
                        self.log(f'[SYNC] Hash del vault actualizado en log: {hash_vault_actual[:16]}...')
                    return True
        
        # Si no existe, crear nuevo registro
        timestamp = datetime.now().strftime("%H:%M:%S")
        nuevo_evento = {
            "time": timestamp,
            "action": f"SYSTEM: [CERRANDO SESIÓN] Hash vault: {hash_vault_actual[:16]}... (total: 131 elementos)"
        }
        
        if log_data:
            log_data[-1]["events"].append(nuevo_evento)
        else:
            # Crear nueva sesión si no existe
            nueva_sesion = {
                "session_number": 1,
                "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "user": "SYSTEM",
                "events": [nuevo_evento]
            }
            log_data.append(nueva_sesion)
        
        with open(ruta_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        if logger:
            logger.log(f'[SYNC] Hash del vault actualizado en log: {hash_vault_actual[:16]}...')
        else:
            self.log(f'[SYNC] Hash del vault actualizado en log: {hash_vault_actual[:16]}...')
        
        return True
    except Exception as e:
        if logger:
            logger.log(f'Error actualizando hash del vault en log: {e}')
        else:
            self.log(f'Error actualizando hash del vault en log: {e}')
        return False

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
    """Extrae el último hash del vault registrado en el log"""
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
                    # Extraer hash del mensaje
                    if 'Hash vault:' in action:
                        hash_part = action.split('Hash vault:')[1].split()[0]
                        return hash_part
        return None
    except Exception:
        return None

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funcionando tanto en desarrollo como en modo empaquetado"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En modo desarrollo
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_data_path(relative_path):
    """Obtiene la ruta a los datos de la aplicación"""
    if hasattr(sys, '_MEIPASS'):
        # Modo empaquetado: los datos están en _internal
        return os.path.join(os.path.dirname(sys.executable), '_internal', relative_path)
    else:
        # Modo desarrollo
        return os.path.join(os.path.abspath("."), relative_path)

def guardar_json_con_hash(ruta, datos, id_elemento=None):
    """
    Guarda un archivo JSON con parámetros estandarizados y genera su hash automáticamente
    
    Args:
        ruta: Ruta del archivo JSON a guardar
        datos: Datos a guardar
        id_elemento: ID del elemento (opcional, se extrae del nombre si no se proporciona)
    
    Returns:
        bool: True si se guardó y generó hash correctamente, False si hubo error
    """
    try:
        # Guardar JSON con parámetros estandarizados
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False, sort_keys=True)
        
        # Extraer ID si no se proporcionó
        if id_elemento is None:
            id_elemento = os.path.basename(ruta).replace('.json', '')
        
        # Generar y guardar hash
        return generar_y_guardar_hash_vault(ruta, id_elemento)
        
    except Exception as e:
        self.log(f"Error guardando JSON con hash: {e}")
        return False
sys.path.append(get_resource_path('core'))
try:
    from indices import generar_indices
except ImportError:
    generar_indices = None

class VentanaPuntos(QDialog):
    # ***<module>.VentanaPuntos: Failure: Different bytecode
    def __init__(self, puntos, calibracion_info=None, parent=None):
        # ***<module>.VentanaPuntos.__init__: Failure: Compilation Error
        super().__init__(parent)
        
        # Configurar tamaño inicial y título
        self.resize(900, 600)
        self.setWindowTitle("Detalle de Puntos de Calibración")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20) # Espaciado pro
        
        # Determinar si es APTO para el estilo
        es_apto = calibracion_info.get('apto', True)
        color_borde = "#569cd6" if es_apto else "#f44336" # Azul o Rojo
        status_text = "CONFORME" if es_apto else "NO CONFORME"
        info_text = f"""
            <div style="background-color: #2d2d30; padding: 15px; border: 2px solid {color_borde}; border-radius: 6px; margin-bottom: 10px;">
                <table width="100%">
                    <tr>
                        <td><span style="color: #569cd6; font-weight: bold;">FECHA:</span> <span style="color: #d4d4d4;">{calibracion_info.get('fecha_calibracion', 'N/A')}</span></td>
                        <td><span style="color: #569cd6; font-weight: bold;">RESPONSABLE:</span> <span style="color: #d4d4d4;">{calibracion_info.get('responsable', 'N/A')}</span></td>
                        <td align="right"><span style="color: {color_borde}; font-weight: bold; font-size: 14px;">ESTADO: {status_text}</span></td>
                    </tr>
                </table>
            </div>
        """
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        self.tabla = QTableWidget()
        # Determinar el número máximo de lecturas para configurar columnas
        max_lecturas = 0
        for p in puntos:
            lecturas_raw = p.get('lecturas', [])
            if isinstance(lecturas_raw, str):
                limpio = lecturas_raw.replace('[', '').replace(']', '').strip()
                lecturas_lista = [x.strip() for x in limpio.split(',') if x.strip()]
                max_lecturas = max(max_lecturas, len(lecturas_lista))
            else:
                max_lecturas = max(max_lecturas, len(lecturas_raw))
        
        # Configurar columnas: fijas + dinámicas para lecturas
        total_columnas = 5 + max_lecturas  # 5 fijas + N lecturas
        self.tabla.setColumnCount(total_columnas)
        
        # Crear headers
        headers = ['Patrón', 'Nominal', 'Media', 'Error', 'Incert.']
        headers.extend([f'L{i+1}' for i in range(max_lecturas)])
        self.tabla.setHorizontalHeaderLabels(headers)
        
        # Configurar modo de redimensionamiento de columnas
        header = self.tabla.horizontalHeader()
        # Columnas fijas se ajustan al contenido
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Columnas de lecturas son elásticas
        for i in range(5, total_columnas):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet('\n            QTableWidget { \n                background-color: #252526; \n                gridline-color: #3e3e42; \n                border: 1px solid #3e3e42; \n            }\n            QHeaderView::section {\n                background-color: #333333;\n                color: #d4d4d4;\n                border: 1px solid #3e3e42;\n                padding: 4px;\n            }\n        ')
        # Establecer el número de filas
        self.tabla.setRowCount(len(puntos))
        
        for i, p in enumerate(puntos):
            lecturas_raw = p.get('lecturas', [])
            media = 0.0
            error = 0.0
            lecturas_lista = []
            
            try:
                if isinstance(lecturas_raw, str):
                    limpio = lecturas_raw.replace('[', '').replace(']', '').strip()
                    lista_nums = [float(x) for x in limpio.split(',') if x.strip()]
                    lecturas_lista = [x.strip() for x in limpio.split(',') if x.strip()]
                else:
                    lista_nums = [float(x) for x in lecturas_raw]
                    lecturas_lista = [str(x) for x in lecturas_raw]
                    
                nominal = float(p.get('valor_nominal', 0))
                media = statistics.mean(lista_nums) if lista_nums else nominal
                error = media - nominal
            except (ValueError, TypeError):
                media = p.get('media', 0.0)
                error = p.get('error', 0.0)
                lecturas_lista = []
            
            # Llenar columnas fijas
            self.tabla.setItem(i, 0, QTableWidgetItem(str(p.get('id_patron', ''))))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(p.get('valor_nominal', ''))))
            self.tabla.setItem(i, 2, QTableWidgetItem(f'{media:.4f}'))
            self.tabla.setItem(i, 3, QTableWidgetItem(f'{error:.4f}'))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(p.get('incertidumbre_k2', ''))))
            
            # Llenar columnas de lecturas individuales
            for j, lectura in enumerate(lecturas_lista):
                if j < max_lecturas:  # No exceder el número de columnas configuradas
                    self.tabla.setItem(i, 5 + j, QTableWidgetItem(str(lectura)))
        
        layout.addWidget(self.tabla)
        
        btn_cerrar = QPushButton('Cerrar')
        btn_cerrar.setFixedHeight(30)
        btn_cerrar.setStyleSheet('background-color: #3e3e42; color: white; border: none;')
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

class VSCIconProvider(QFileIconProvider):
    def icon(self, info):
        # 1. CARPETAS
        if info.isDir():
            # Usamos un azul estilo VS Code para las carpetas
            return qta.icon('fa5s.folder', color='#007acc')

        # 2. ARCHIVOS (Obtenemos la extensión)
        file_info = info.suffix().lower()
        
        if file_info == 'py':
            return qta.icon('fab.python', color='#3776ab')
        
        elif file_info == 'pdf':
            return qta.icon('fa5s.file-pdf', color='#e74c3c')
        
        elif file_info == 'json':
            # Un color amarillo/dorado para los datos
            return qta.icon('fa5s.code', color='#f1c40f')
        
        elif file_info in ['png', 'jpg', 'jpeg']:
            return qta.icon('fa5s.file-image', color='#a074c4')
        
        else:
            # Icono por defecto para el resto
            return qta.icon('fa5.file', color='#cccccc')
            
class SelectorAdmin(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Panel de Control - Administrador')
        self.setFixedSize(400, 280)  # Aumentado para el tercer botón
        self.choice = None
        self.setStyleSheet('\n            QDialog {\n                background-color: #1e1e1e;\n                color: #ffffff;\n                border: 1px solid #333333;\n                border-radius: 8px;\n            }\n            QLabel {\n                color: #cccccc;\n                font-size: 14px;\n                margin-bottom: 15px;\n            }\n            QPushButton {\n                background-color: #1a1a1a;\n                border: 1px solid #0078d4;\n                border-radius: 4px;\n                color: #0078d4;\n                padding: 12px;\n                font-weight: bold;\n                font-size: 14px;\n                margin: 5px;\n            }\n            QPushButton:hover {\n                background-color: #0078d4;\n                color: white;\n            }\n            QPushButton:pressed {\n                background-color: #005a9e;\n            }\n        ')
        layout = QVBoxLayout()
        label = QLabel('Acceso de Administrador Detectado\n¿Qué desea realizar?')
        label.setStyleSheet('font-size: 14px; font-weight: bold; color: white; margin: 10px;')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_app = QPushButton('ENTRAR A METROLOGÍA')
        btn_app.setMinimumHeight(60)
        btn_app.clicked.connect(self.choose_app)
        btn_users = QPushButton('GESTIONAR USUARIOS')
        btn_users.setMinimumHeight(60)
        btn_users.clicked.connect(self.choose_users)
        btn_audit = QPushButton('AUDITORÍA E INTEGRIDAD')
        btn_audit.setMinimumHeight(60)
        btn_audit.clicked.connect(self.choose_audit)
        layout.addWidget(label)
        layout.addWidget(btn_app)
        layout.addWidget(btn_users)
        layout.addWidget(btn_audit)
        self.setLayout(layout)

    def choose_app(self):      
        self.choice = 'app'
        self.accept()

    def choose_users(self):
        self.choice = 'users'
        self.accept()

    def choose_audit(self):
        self.choice = 'audit'
        self.accept()

class MetrologiaApp(QMainWindow):
    # ***<module>.MetrologiaApp: Failure detected at line number 809 and instruction offset 302: Different bytecode
    def __init__(self):
        super().__init__()
        
        # 1. Inicialización de datos y Logger
        if generar_indices:
            try:
                generar_indices()
            except Exception as e:
                self.log(f'Error al refrescar índices: {e}')
        
        self.logger = init_logger()
        
        # Verificar integridad del log al iniciar
        if not self.verificar_integridad_log():
            # Si el usuario eligió "No" en el modal, cerrar la aplicación
            self._salida_por_error_verificacion = True
            self.close()
            sys.exit()
        
        # Verificar integridad del número de sesión
        if not self.verificar_numero_sesion():
            # Si el usuario eligió "No" en el modal, cerrar la aplicación
            self._salida_por_error_verificacion = True
            self.close()
            sys.exit()
        
        self.current_user = None
        self.current_user_data = None
        self.user_type = None
        self.current_familia = None
        
        # 2. Configuración Visual
        self.setWindowTitle('METROLOGY CORE 2026')
        self.setStyleSheet(STYLE_SHEET)
        self.colores_familia = ['Rojo', 'Azul', 'Verde', 'Naranja', 'Purpura', 'Rosa', 'Cian']
        self.familia_colores = {}

        # 3. Interfaz de Pestañas (Main Tabs)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 1. INSTRUMENTOS (primera pestaña)
        self.page_instrumentos = QWidget()
        
        # 2. PATRONES (segunda pestaña)
        self.page_patrones = QWidget()
        self.setup_page_patrones()
        
        # 3. CALENDARIO (tercera pestaña)
        self.page_proximos = QWidget()
        self.setup_page_proximos()
        
        # Crear páginas de navegación que faltan (para uso interno en stacks)
        # self.page_familias ya no se necesita, se maneja en setup_page_instrumentos
        
        # Crear páginas ANTES de configurarlas
        self.page_detalle = QWidget()
        self.page_ficha_tecnica = QWidget()
        
        # Ahora configurar las páginas
        self.setup_page_detalle()
        self.setup_page_ficha_tecnica()
        self.setup_page_instrumentos()  # ← Ahora sí existe page_detalle
        
        # Agregar pestañas en orden: Instrumentos, Patrones, Calendario
        self.tab_widget.addTab(self.page_instrumentos, '🔧 INSTRUMENTOS')
        self.tab_widget.addTab(self.page_patrones, '📏 PATRONES')
        self.tab_widget.addTab(self.page_proximos, '📋 CALENDARIO')
        
        # Iniciar en la pestaña de instrumentos (índice 0)
        self.tab_widget.setCurrentIndex(0)
        
        self.setCentralWidget(self.tab_widget)
        
        # 4. Configuración de Consola
        self.setup_console()
        
        # 4.1. Configuración del Árbol Explorador
        self.setup_tree()
        
        self.refresh_bento_view()
        
        self.tab_widget.currentChanged.connect(self.actualizar_menu_contextual)
        self.showMaximized()

        # 5. LÓGICA DE LOGIN (Aquí estaba el fallo de 'is None')
        self.efecto_borroso = QGraphicsBlurEffect()
        self.efecto_borroso.setBlurRadius(15)
        self.setGraphicsEffect(self.efecto_borroso)

        login_dialog = LoginDialog(self)
        # CORRECCIÓN: exec() devuelve 1 (True) si el login fue exitoso
        if login_dialog.exec(): 
            self.current_user = login_dialog.get_username()
            self.current_user_data = login_dialog.get_user_data()
            self.user_type = login_dialog.get_user_type()
            
            self.logger.set_user(self.current_user)
            self.logger.log_event('AUTH', f'Acceso con rol: {self.user_type}', 'info')
            
            # Incrementar sesión DESPUÉS del login exitoso
            from core.session_manager import incrementar_sesion
            nueva_sesion = incrementar_sesion()
            if nueva_sesion:
                self.log(f'[INFO] Sesión incrementada a: {nueva_sesion}')
            else:
                self.log('[ERROR] No se pudo incrementar la sesión')
            
            # 6. Verificar integridad individual de elementos DESPUÉS del login
            self.log('[INFO] Verificando integridad de elementos individuales...')
            elementos_comprometidos = self.verificar_integridad_elementos_al_inicio()
            
            if elementos_comprometidos:
                self.mostrar_ventana_elementos_comprometidos(elementos_comprometidos)
            
            # Quitar efecto borroso al entrar
            self.setGraphicsEffect(None)
            if hasattr(self, 'console') and self.console is not None:
                self.console.clear()

            if self.current_user == 'admin':
                self.log('[ADMIN] Detectado acceso de administrador.')
                # Si tienes SelectorAdmin definido:
                if 'SelectorAdmin' in globals() or hasattr(self, 'SelectorAdmin'):
                    selector = SelectorAdmin(self)
                    if selector.exec():
                        if getattr(selector, 'choice', None) == 'users':
                            self.abrir_gestion_usuarios()
                        elif getattr(selector, 'choice', None) == 'audit':
                            self.abrir_auditoria_integridad()
                
            self.log(f'Sesión iniciada como {self.current_user}')
            self.logger.log_navigation('Login', 'Panel Principal', self.current_user)
        else:
            # Si cancela el login, cerramos la app
            self.close()
            sys.exit()   

    def closeEvent(self, event):
        """Versión corregida: El visor cierra legítimamente pero preserva problemas del vault"""
        import time
        try:
            # Si somos visor, cerramos legítimamente PERO preservando problemas existentes
            es_visor = getattr(self, 'user_type', '').lower() == 'visor'
            
            if es_visor:
                # Registrar evento específico de cierre de visor para detección
                self.log('[VIEWER] Cierre de sesión en modo visor - cerrando legítimamente')
                
                # El visor SÍ guarda hash del log (para evitar falsa alerta) PERO NO toca el vault
                ruta_log = 'metrologia_log.json'
                ruta_hash_log = 'metrologia_log.hash'
                
                if os.path.exists(ruta_log):
                    self.log('[VIEWER] Sellando log de auditoría (cierre legítimo de visor)...')
                    hash_log = generar_hash_archivo(ruta_log)
                    
                    with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                        f.write(hash_log)
                    
                    self.log(f'[VIEWER] Log sellado para próxima sesión: {hash_log[:8]}...')
                
                # Incrementar sesión
                from core.session_manager import incrementar_sesion
                nueva_sesion = incrementar_sesion()
                if nueva_sesion:
                    self.log(f'[VIEWER] Sesión incrementada: {nueva_sesion}')
                
                event.accept()
                return
            
            # Solo usuarios NO visores pueden modificar integridad del vault
            # 1. Generar vault de datos
            # Solo si NO hay discrepancia previa, actualizamos los hashes de los instrumentos
            if not hasattr(self, '_salida_por_discrepancia'):
                self.log('[INFO] Actualizando integridad de archivos JSON...')
                hash_vault, total_elementos = generar_vault_completo()
                if hash_vault:
                    self.logger.log_hash_vault(hash_vault, total_elementos, "SESION")
            else:
                self.log('[WARNING] Hay discrepancia previa - NO se actualizan hashes de datos para proteger integridad')
            
            # 2. Usuarios NO visores sellan el log
            ruta_log = 'metrologia_log.json'
            ruta_hash_log = 'metrologia_log.hash'
            
            if os.path.exists(ruta_log):
                self.log('[INFO] Sellando log de auditoría antes de salir...')
                hash_log = generar_hash_archivo(ruta_log)
                
                with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                    f.write(hash_log)
                
                self.log(f'[HASH] Log validado para próxima sesión: {hash_log[:8]}...')
            
            # Incrementar sesión para mantener consistencia
            from core.session_manager import incrementar_sesion
            nueva_sesion = incrementar_sesion()
            if nueva_sesion:
                self.log(f'[INFO] Sesión incrementada: {nueva_sesion}')
            
            event.accept()
        except Exception as e:
            self.log(f'[ERROR] Error en cierre: {str(e)}')
            event.accept()

    def mostrar_ventana_discrepancia_hash(self, titulo, mensaje_principal, mensaje_secundario, tipo_elemento=None, id_elemento=None):
        msg_box = QMessageBox(self)
        
        # Usamos shield-alt con un color naranja-amarillo para dar sensación de alerta de seguridad
        icon = qta.icon('fa5s.shield-alt', color='#FFD700') # Oro / Amarillo fuerte
        msg_box.setWindowIcon(icon)
        msg_box.setIconPixmap(icon.pixmap(64, 64))
        
        msg_box.setWindowTitle(titulo)
        # Mensaje principal con acento amarillo
        msg_box.setText(f"<p style='color: #FFD700; font-size: 16px; font-weight: bold;'>{mensaje_principal}</p>")
        msg_box.setInformativeText(mensaje_secundario)
        
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Retry
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Personalización de botones
        btn_si = msg_box.button(QMessageBox.StandardButton.Yes)
        btn_no = msg_box.button(QMessageBox.StandardButton.No)
        btn_retry = msg_box.button(QMessageBox.StandardButton.Retry)
        
        btn_no.setText("❌ Salir")
        btn_retry.setText("🔑 Restaurar (Admin)")
        
        if tipo_elemento == 'log':
            btn_si.setText("⚠️ Continuar con Riesgo")
        else:
            btn_si.setText("👁️ Modo Visor")

        # --- CSS CON ACENTO Y BARRA SIMULADA ---
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #1a1a1a;
                /* La barra amarilla simulada en la parte superior */
                border-top: 15px solid #FFD700; 
                border-left: 1px solid #333;
                border-right: 1px solid #333;
                border-bottom: 1px solid #333;
                min-width: 450px;
            }}
            QLabel {{
                color: #ffffff;
                font-family: 'Segoe UI';
                padding: 10px;
            }}
            /* Estilo para el texto secundario */
            QLabel#qt_msgbox_informativetext {{
                color: #bbbbbb;
                font-size: 13px;
            }}
            QPushButton {{
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 2px;
                color: white;
                margin-bottom: 10px;
            }}
            /* Botón Continuar / Visor */
            QPushButton[text*="Continuar"], QPushButton[text*="Visor"] {{
                background-color: #333333;
                border: 1px solid #FFD700; /* Borde amarillo para resaltar el acento */
            }}
            QPushButton:hover {{ background-color: #444444; }}
            
            /* Botón Salir (Rojo oscuro) */
            QPushButton[text*="Salir"] {{
                background-color: #441111;
                border: 1px solid #cc3333;
            }}
            
            /* Botón Admin (Verde Defender) */
            QPushButton[text*="Restaurar"] {{
                background-color: #113311;
                border: 1px solid #2ecc71;
            }}
        """)
        
        res = msg_box.exec()
        
        if res == QMessageBox.StandardButton.Retry: return 'regenerar'
        if res == QMessageBox.StandardButton.Yes: return 'continuar'
        if res == QMessageBox.StandardButton.No: return 'cancelar'
        return 'cancelar'  # Por defecto

    def _ultimo_cierre_fue_visor(self):
        """Verifica si el último evento en el log fue un cierre de visor"""
        try:
            ruta_log = 'metrologia_log.json'
            if not os.path.exists(ruta_log):
                return False
                
            with open(ruta_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # Buscar el último evento de la última sesión
            if log_data and len(log_data) > 0:
                ultima_sesion = log_data[-1]
                eventos = ultima_sesion.get('events', [])
                
                if eventos and len(eventos) > 0:
                    ultimo_evento = eventos[-1]
                    action = ultimo_evento.get('action', '')
                    
                    # Buscar indicadores de cierre de visor
                    if '[VIEWER]' in action and 'Cierre de sesión en modo visor' in action:
                        return True
                        
            return False
        except Exception as e:
            self.log(f'[ERROR] Error verificando último cierre: {e}')
            return False

    def verificar_integridad_log(self):
        """Flujo mejorado: Detecta si el último cierre fue de un visor para evitar falsos positivos"""
        # 1. Verificar integridad del log usando su hash guardado
        self.log('[INFO] Verificando integridad del log...')
        ruta_log = 'metrologia_log.json'
        ruta_hash_log = 'metrologia_log.hash'
        
        if not os.path.exists(ruta_log):
            self.log('[INFO] No existe archivo de log (primera ejecución)')
            # Crear hash inicial del log vacío
            hash_inicial = generar_hash_archivo(ruta_log)
            with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                f.write(hash_inicial)
            self.log(f'[INFO] Hash inicial del log creado: {hash_inicial[:16]}...')
        elif not os.path.exists(ruta_hash_log):
            self.log('[INFO] No existe hash del log (primera ejecución)')
            # Crear hash del log existente
            hash_actual = generar_hash_archivo(ruta_log)
            with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                f.write(hash_actual)
            self.log(f'[INFO] Hash del log creado: {hash_actual[:16]}...')
        else:
            try:
                # Leer hash guardado
                with open(ruta_hash_log, 'r', encoding='utf-8') as f:
                    hash_guardado = f.read().strip()
                
                # Generar hash actual
                hash_actual = generar_hash_archivo(ruta_log)
                
                if hash_actual == hash_guardado:
                    self.log('[INFO] Integridad del log verificada')
                else:
                    # VERIFICACIÓN MEJORADA: ¿El último cierre fue de un visor?
                    if self._ultimo_cierre_fue_visor():
                        self.log('[INFO] Log modificado por visor - esto es esperado y seguro')
                        # Regenerar el hash para mantener consistencia
                        with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                            f.write(hash_actual)
                        self.log('[SYNC] Hash del log actualizado tras cierre de visor')
                    else:
                        self.log('[SECURITY] ⚠️ LOG MODIFICADO EXTERNAMENTE')
                        
                        resultado = self.mostrar_ventana_discrepancia_hash(
                            titulo="🚨 LOG COMPROMETIDO",
                            mensaje_principal="El archivo de auditoría ha sido modificado externamente",
                            mensaje_secundario="El log de auditoría no coincide con su hash guardado.\n\nEsto podría indicar manipulación maliciosa del sistema.\n\n¿Desea continuar bajo su propio riesgo?",
                            tipo_elemento='log'
                        )
                    
                    if resultado == 'cancelar':
                        return False
                    elif resultado == 'continuar':
                        self.log('[WARNING] Continuando con log modificado - RIESGO DE SEGURIDAD')
                    elif resultado == 'regenerar':
                        admin_user = self.solicitar_admin_para_regenerar_hash('log')
                        if admin_user:
                            # Obtener nombre completo del usuario
                            nombre_completo = self.obtener_nombre_completo_usuario(admin_user)
                            # Regenerar hash del log
                            with open(ruta_hash_log, 'w', encoding='utf-8') as f:
                                f.write(hash_actual)
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            self.log(f'[RESTAURADA POR] {nombre_completo} restaurado hash log - {timestamp}')
                            if hasattr(self, 'logger') and self.logger:
                                self.logger.log_security_event('SECURITY', f'Hash del log restaurado por administrador {nombre_completo}', 'warning')
                            else:
                                self.log('[ERROR] Logger no disponible para registrar evento de seguridad')
                        else:
                            return False
                    
            except Exception as e:
                self.log(f'[ERROR] Error verificando log: {str(e)}')
                return False
        
        # 2. Verificar session_counter
        self.log('[INFO] Verificando session_counter...')
        session_ok, session_msg = verificar_session_counter()
        
        if not session_ok:
            self.log(f'[SECURITY] ⚠️ {session_msg}')
            resultado = self.mostrar_ventana_discrepancia_hash(
                titulo="⚠️ Problema con Session Counter",
                mensaje_principal="Se ha detectado un problema en el contador de sesiones",
                mensaje_secundario=f"{session_msg}\n\n¿Desea continuar o restaurar como administrador?",
                tipo_elemento='session_counter'
            )
            
            if resultado == 'cancelar':
                return False
        else:
            self.log(f'[INFO] {session_msg}')
        
        # 3. Verificar integridad del vault contra hash guardado en log
        self.log('[INFO] Verificando integridad del vault...')
        vault = cargar_vault_hashes()
        
        if not vault:
            self.log('[SECURITY] ⚠️ VAULT INEXISTENTE - Posible manipulación o eliminación')
            resultado = self.mostrar_ventana_discrepancia_hash(
                titulo="🚨 VAULT INEXISTENTE",
                mensaje_principal="El archivo de vault de hashes no existe",
                mensaje_secundario="El vault de hashes ha sido eliminado o nunca ha sido creado.\n\nEsto podría indicar manipulación maliciosa del sistema.\n\nSe requiere intervención del administrador para regenerar el vault.",
                tipo_elemento='vault'
            )
            
            if resultado == 'cancelar':
                self._salida_por_discrepancia = True
                return False
            elif resultado == 'regenerar':
                # Solicitar credenciales de administrador para regenerar
                admin_user = self.solicitar_admin_para_regenerar_hash('vault')
                if admin_user:
                    # Obtener nombre completo del usuario
                    nombre_completo = self.obtener_nombre_completo_usuario(admin_user)
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log(f'[RESTAURADA POR] {nombre_completo} autorizado regeneración vault - {timestamp}')
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.log_security_event('SECURITY', f'Vault inexistente regenerado por administrador {nombre_completo}', 'warning')
                    else:
                        self.log('[ERROR] Logger no disponible para registrar evento de seguridad')
                    
                    # Generar vault completo
                    vault_generado, total_elementos = generar_vault_completo()
                    if vault_generado:
                        self.log(f'[RESTAURADA POR] {nombre_completo} - Vault regenerado: {total_elementos} elementos - {timestamp}')
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.log_security_event('SECURITY', f'Vault regenerado completamente ({total_elementos} elementos) por administrador {nombre_completo}', 'warning')
                        else:
                            self.log('[ERROR] Logger no disponible para registrar evento de seguridad')
                    else:
                        self.log('[ERROR] No se pudo regenerar el vault')
                        return False
                else:
                    self._salida_por_discrepancia = True
                    return False
            else:
                    # Continuar sin vault - NO establecer salida por discrepancia
                    self.log('[WARNING] Usuario eligió continuar sin vault - funcionamiento limitado')
                    return False
        
        # Verificar que todos los elementos sean hashes válidos
        elementos_invalidos = []
        for key, hash_val in vault.items():
            if not isinstance(hash_val, str) or len(hash_val) != 64:
                elementos_invalidos.append(key)
        
        if elementos_invalidos:
            self.log(f'[ERROR] Vault contiene {len(elementos_invalidos)} elementos inválidos')
            return False
        else:
            self.log(f'[INFO] Vault íntegro ({len(vault)} elementos)')
        
        # 4. Verificar hash del vault contra el guardado en el log
        hash_vault_actual = generar_hash_vault()
        hash_vault_log = obtener_ultimo_hash_vault_del_log()
        
        if hash_vault_actual and hash_vault_log:
            if hash_vault_log.endswith('...'):
                # Hash truncado del log - comparar primeros 16 caracteres
                if hash_vault_actual.startswith(hash_vault_log.replace('...', '')):
                    self.log('[INFO] Integridad del vault verificada contra log')
                else:
                    self.log('[SECURITY] ⚠️ DISCREPANCIA: Vault modificado externamente')
                    self.log(f'[SECURITY] Hash guardado: {hash_vault_log}')
                    self.log(f'[SECURITY] Hash actual: {hash_vault_actual[:16]}...')
                    
                    resultado = self.mostrar_ventana_discrepancia_hash(
                        titulo="🚨 VAULT COMPROMETIDO",
                        mensaje_principal="Se ha detectado manipulación del vault de hashes",
                        mensaje_secundario=f"El vault ha sido modificado externamente entre sesiones.\n\nHash anterior: {hash_vault_log}\nHash actual: {hash_vault_actual[:16]}...\n\nEsto podría indicar manipulación maliciosa de archivos de datos.\n\n¿Desea continuar bajo su propio riesgo?",
                        tipo_elemento='vault'
                    )
                    
                    if resultado == 'cancelar':
                        return False
            else:
                # Hash completo del log - comparación exacta
                if hash_vault_actual == hash_vault_log:
                    self.log('[INFO] Integridad del vault verificada contra log')
                else:
                    self.log('[SECURITY] ⚠️ DISCREPANCIA: Vault modificado externamente')
                    resultado = self.mostrar_ventana_discrepancia_hash(
                        titulo="🚨 VAULT COMPROMETIDO",
                        mensaje_principal="Se ha detectado manipulación del vault de hashes",
                        mensaje_secundario=f"El vault ha sido modificado externamente entre sesiones.\n\nHash anterior: {hash_vault_log}\nHash actual: {hash_vault_actual[:16]}...\n\nEsto podría indicar manipulación maliciosa de archivos de datos.\n\n¿Desea continuar bajo su propio riesgo?",
                        tipo_elemento='vault'
                    )
                    
                    if resultado == 'cancelar':
                        return False
        else:
            self.log('[INFO] No hay hash anterior del vault para comparar (primera ejecución)')
        
        # 5. Si todo está OK, continuar con el flujo normal
        self.log('[INFO] ✅ Sistema verificado correctamente - listo para operar')
        return True
    
    def verificar_integridad_elementos_al_inicio(self):
        """Verifica todos los elementos y devuelve lista de IDs comprometidos (máx 5)"""
        try:
            vault = cargar_vault_hashes()
            elementos_comprometidos = []
            
            for id_elemento, hash_guardado in vault.items():
                # Buscar el archivo JSON del elemento
                ruta_elemento = None
                for rama in ['instrumentos', 'patrones']:
                    base_path = get_data_path(os.path.join('data', rama))
                    if os.path.exists(base_path):
                        for fam in os.listdir(base_path):
                            ruta_fam = os.path.join(base_path, fam)
                            ruta_elem = os.path.join(ruta_fam, id_elemento, f"{id_elemento}.json")
                            if os.path.exists(ruta_elem):
                                ruta_elemento = ruta_elem
                                break
                        if ruta_elemento:
                            break
                
                if ruta_elemento:
                    # Verificar hash del archivo
                    hash_actual = generar_hash_archivo(ruta_elemento)
                    if hash_actual != hash_guardado:
                        elementos_comprometidos.append(id_elemento)
                        self.log(f'[SECURITY] ⚠️ Elemento comprometido: {id_elemento}')
                        
                        # Limitar a 5 elementos para no saturar
                        if len(elementos_comprometidos) >= 5:
                            self.log(f'[WARNING] Demasiados elementos comprometidos, mostrando solo los primeros 5')
                            break
            
            if elementos_comprometidos:
                self.log(f'[SECURITY] 🚨 Se detectaron {len(elementos_comprometidos)} elementos comprometidos')
            else:
                self.log('[INFO] Todos los elementos tienen integridad verificada')
            
            return elementos_comprometidos
            
        except Exception as e:
            self.log(f'[ERROR] Error verificando integridad de elementos: {e}')
            return []
    
    def mostrar_ventana_elementos_comprometidos(self, elementos_comprometidos):
        """Muestra ventana con elementos comprometidos y opciones de recuperación (estilo ventana de log)"""
        try:
            # Importar iconos
            import qtawesome as qta
            
            msg_box = QMessageBox(self)
            
            # Usamos shield-alt con un color naranja-amarillo para dar sensación de alerta de seguridad
            icon = qta.icon('fa5s.shield-alt', color='#FFD700') # Oro / Amarillo fuerte
            msg_box.setWindowIcon(icon)
            msg_box.setIconPixmap(icon.pixmap(64, 64))
            
            msg_box.setWindowTitle("🛡️ INTEGRIDAD COMPROMETIDA")
            
            # Construir mensaje principal
            if len(elementos_comprometidos) == 1:
                mensaje_principal = f"Se ha detectado 1 elemento con integridad comprometida"
                elementos_text = f"• {elementos_comprometidos[0]}"
            else:
                mensaje_principal = f"Se han detectado {len(elementos_comprometidos)} elementos con integridad comprometida"
                elementos_text = "\n• ".join(elementos_comprometidos)
                if len(elementos_comprometidos) >= 5:
                    elementos_text += "\n• ... (y posiblemente más)"
            
            # Mensaje principal con acento amarillo
            msg_box.setText(f"<p style='color: #FFD700; font-size: 16px; font-weight: bold;'>{mensaje_principal}</p>")
            
            # Mensaje secundario con detalles
            mensaje_secundario = f"Los siguientes archivos han sido modificados externamente:\n\n{elementos_text}\n\nEsto podría indicar manipulación maliciosa de datos.\n\n¿Desea continuar bajo su propio riesgo o restaurar la integridad?"
            msg_box.setInformativeText(mensaje_secundario)
            
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No | 
                QMessageBox.StandardButton.Retry
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            # Personalización de botones
            btn_continuar = msg_box.button(QMessageBox.StandardButton.Yes)
            btn_salir = msg_box.button(QMessageBox.StandardButton.No)
            btn_restaurar = msg_box.button(QMessageBox.StandardButton.Retry)
            
            btn_continuar.setText("⚠️ Continuar con Riesgo")
            btn_salir.setText("❌ Salir")
            btn_restaurar.setText("🔑 Restaurar (Admin)")
            
            # --- CSS CON ACENTO Y BARRA SIMULADA (idéntico a ventana de log) ---
            msg_box.setStyleSheet(f"""
                QMessageBox {{
                    background-color: #1a1a1a;
                    /* Línea más fina = menos problemas */
                    border-top: 10px solid #FFD700; 
                    border-left: 1px solid #333;
                    border-right: 1px solid #333;
                    border-bottom: 1px solid #333;
                    min-width: 450px;
                }}
                
                QLabel {{
                    color: #ffffff;
                    font-family: 'Segoe UI';
                    /* Bajamos un poco los widgets para que no peguen al borde */
                    padding-top: 15px;
                    padding-left: 10px;
                    padding-right: 10px;
                }}

                /* Bajamos un pelo más el texto principal para separarlo de la línea */
                QLabel#qt_msgbox_label {{
                    margin-top: 5px;
                    color: #FFD700;
                    font-weight: bold;
                }}

                QPushButton {{
                    font-weight: bold;
                    padding: 8px 16px;
                    color: white;
                    margin-top: 10px;
                    margin-bottom: 5px;
                }}
                
                QPushButton[text*="Continuar"] {{ background-color: #333; border: 1px solid #FFD700; }}
                QPushButton[text*="Salir"] {{ background-color: #441111; border: 1px solid #cc3333; }}
                QPushButton[text*="Restaurar"] {{ background-color: #113311; border: 1px solid #2ecc71; }}
            """)
            
            resultado = msg_box.exec()
            
            if msg_box.clickedButton() == btn_salir:
                self.log('[SECURITY] Usuario eligió salir por integridad comprometida')
                self._salida_por_error_verificacion = True
                # Cerrar normalmente para que se ejecute closeEvent y genere el hash final
                self.close()
                # Forzar salida completa después del cierre normal
                sys.exit()
            elif msg_box.clickedButton() == btn_restaurar:
                self.log('[SECURITY] Usuario eligió restaurar - solicitando credenciales de administrador')
                admin_user = self.solicitar_admin_para_restaurar()
                if admin_user:
                    self.log(f'[RESTAURACIÓN] {admin_user} ha autorizado la restauración del vault - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                    self.logger.log_event('SECURITY', f'Restauración del vault autorizada por {admin_user}', 'warning')
                    self.restaurar_integridad_vault()
                else:
                    self.log('[WARNING] Restauración cancelada - credenciales incorrectas')
            else:  # btn_continuar
                self.log('[WARNING] Usuario eligió continuar con elementos comprometidos - cambiando a rol VISOR')
                # Cambiar a rol visor para proteger integridad de datos
                self.current_user = 'visor'
                self.user_type = 'visor'
                self.log(f'[SECURITY] Rol cambiado a VISOR por integridad comprometida - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                self.logger.log_security_event('SECURITY', 'Usuario cambiado a rol VISOR por elementos comprometidos', 'warning')
                
        except Exception as e:
            self.log(f'[ERROR] Error mostrando ventana de elementos comprometidos: {e}')
    
    def solicitar_admin_para_restaurar(self):
        """Solicita credenciales de administrador para restaurar integridad"""
        from gui.login_dialog import LoginDialog
        
        login_dialog = LoginDialog(self)
        login_dialog.setWindowTitle("🔐 Autenticación de Administrador - Restaurar Integridad")
        login_dialog.header.setText("Se requieren credenciales de administrador para restaurar la integridad del vault")
        
        if login_dialog.exec():
            username = login_dialog.get_username()
            user_type = login_dialog.get_user_type()
            
            # Verificar que sea administrador
            if username == 'admin' and user_type == 'tecnicos':
                return True
            else:
                QMessageBox.warning(self, "Acceso Denegado", "Se requieren credenciales de administrador para esta acción.")
                return False
        return False
    
    def restaurar_integridad_vault(self):
        """Regenera el vault completo con los hashes actuales de todos los elementos"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log(f'[RESTAURACIÓN] Iniciando restauración completa del vault - {timestamp}')
            
            # Generar nuevo vault completo
            hash_vault, total_elementos = generar_vault_completo()
            
            if hash_vault:
                self.log(f'[RESTAURACIÓN] Vault restaurado exitosamente - {total_elementos} elementos procesados - Hash: {hash_vault[:16]}...')
                self.logger.log_event('SECURITY', f'Vault restaurado completamente ({total_elementos} elementos)', 'warning')
                
                QMessageBox.information(self, "✅ Integridad Restaurada", 
                    f"El vault ha sido regenerado exitosamente.\n\nTotal elementos: {total_elementos}\nHash: {hash_vault[:16]}...")
                
                self.log(f'[RESTAURACIÓN] ✅ Vault restaurado completamente - {timestamp}')
            else:
                QMessageBox.critical(self, "Error", "No se pudo regenerar el vault.")
                self.log('[ERROR] Falló la regeneración del vault')
                
        except Exception as e:
            self.log(f'[ERROR] Error restaurando integridad: {e}')
            QMessageBox.critical(self, "Error", f"Error durante la restauración: {str(e)}")

    def guardar_incidente_seguridad(self, incidente):
        """
        Guarda un incidente de seguridad en el log de forma persistente.
        Asegura la escritura física en disco antes de cualquier otra acción.
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            time_part = timestamp.split('T')[1]
            descripcion = incidente.get('descripcion', 'Sin descripción')
            motivo = incidente.get('motivo', 'Desconocido')
            accion = incidente.get('accion', 'NOTIFICADA')
            
            ruta_log = 'metrologia_log.json'
            
            # 1. Preparar el bloque de la "sesión de incidente"
            # Usamos un session_number único para que no choque con los enteros
            nueva_entrada = {
                "session_number": f"INCIDENT_{timestamp.replace(':', '')}",
                "start_time": timestamp,
                "user": "SYSTEM",
                "events": [
                    {
                        "time": time_part,
                        "action": f"SECURITY: {descripcion}",
                        "detail": f"Motivo: {motivo} | Acción: {accion}"
                    }
                ]
            }

            # 2. Leer y reconstruir el archivo
            if os.path.exists(ruta_log):
                with open(ruta_log, 'r', encoding='utf-8') as f:
                    contenido = f.read().strip()
                
                # Limpieza quirúrgica del final del JSON para insertar
                if contenido.endswith(']'):
                    # Eliminamos el último corchete para "abrir" el array
                    contenido_sin_cierre = contenido[:contenido.rfind(']')]
                    
                    # Verificamos si ya hay contenido para poner la coma
                    separador = "," if contenido_sin_cierre.strip().endswith('}') else ""
                    
                    import json
                    bloque_json = json.dumps(nueva_entrada, indent=2, ensure_ascii=False)
                    # Formateamos el bloque para que encaje con la indentación
                    contenido_final = f"{contenido_sin_cierre}{separador}\n{bloque_json}\n]"
                else:
                    # Si el archivo está corrupto (no termina en ]), lo tratamos como nuevo
                    import json
                    contenido_final = json.dumps([nueva_entrada], indent=2, ensure_ascii=False)
            else:
                # Si el log no existe, creamos el array desde cero
                import json
                contenido_final = json.dumps([nueva_entrada], indent=2, ensure_ascii=False)

            # 3. ESCRITURA BLINDADA (Atomic-ish)
            with open(ruta_log, 'w', encoding='utf-8') as f:
                f.write(contenido_final)
                f.flush()            # Volcar buffer de Python al SO
                os.fsync(f.fileno()) # Forzar al disco duro a escribir físicamente

            self.log(f'[SECURITY] Incidente registrado físicamente: {descripcion}')
            return True

        except Exception as e:
            # Si esto falla, intentamos al menos un log de emergencia en texto plano
            try:
                with open('emergency_security.log', 'a', encoding='utf-8') as f_em:
                    f_em.write(f"[{datetime.now()}] ERROR CRÍTICO AL GRABAR JSON: {descripcion}\n")
            except:
                pass
            self.log(f'[ERROR] Fallo crítico al guardar incidente: {e}')
            return False

    def verificar_integridad_elemento(self, ruta_json, id_elemento, tipo_elemento='elemento'):
        """
        Verifica la integridad de un elemento (instrumento o patrón) usando ventana unificada
        
        Args:
            ruta_json: Ruta al archivo JSON del elemento
            id_elemento: ID del elemento
            tipo_elemento: 'elemento' o 'patron'
        
        Returns:
            True si se puede continuar, False si se cancela
        """
        # Usar la función global para verificar integridad
        integridad_ok, mensaje = verificar_integridad_archivo_vault(ruta_json, id_elemento)
        
        if not integridad_ok:
            # Usar ventana unificada
            resultado = self.mostrar_ventana_discrepancia_hash(
                titulo="⚠️ Discrepancia de Integridad",
                mensaje_principal=f"Se ha detectado una discrepancia en el {tipo_elemento} {id_elemento}",
                mensaje_secundario=f"{mensaje}\n\n¿Desea continuar cargando el elemento o regenerar el hash como administrador?",
                tipo_elemento=tipo_elemento,
                id_elemento=id_elemento
            )
            
            if resultado == 'cancelar':
                self.log(f'[INFO] Carga cancelada por discrepancia en {tipo_elemento} {id_elemento}')
                return False
            elif resultado == 'regenerar':
                # Solicitar credenciales de administrador
                if self.solicitar_admin_para_regenerar_hash(tipo_elemento):
                    # Regenerar hash del elemento
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if generar_y_guardar_hash_vault(ruta_json, id_elemento):
                        # Obtener nombre completo del usuario
                        nombre_completo = self.obtener_nombre_completo_usuario('admin')
                        self.log(f'[RESTAURADA POR] {tipo_elemento} {id_elemento} regenerado - {timestamp}')
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.log_security_event('SECURITY', f'Hash de {tipo_elemento} {id_elemento} regenerado por administrador {nombre_completo}', 'warning')
                        else:
                            self.log('[ERROR] Logger no disponible para registrar evento de seguridad')
                        return True
                    else:
                        self.log(f'[ERROR] No se pudo regenerar hash del {tipo_elemento} {id_elemento}')
                        return False
                else:
                    return False
            else:  # cargar
                self.log(f'[ADVERTENCIA] Cargando {tipo_elemento} {id_elemento} con discrepancia de hash')
                return True
        
        return True  # Si la integridad es correcta

    def obtener_nombre_completo_usuario(self, username):
        """Obtiene el nombre completo del usuario desde config/users.json"""
        try:
            with open('config/users.json', 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            # Buscar en técnicos y visores
            for categoria in ['tecnicos', 'visor']:
                if categoria in users_data:
                    for user in users_data[categoria]:
                        if user.get('username') == username:
                            return user.get('nombre_completo', username)
            
            return username  # Si no encuentra, devuelve el username
        except Exception as e:
            self.log(f'[ERROR] Error obteniendo nombre completo: {e}')
            return username

    def solicitar_admin_para_regenerar_hash(self, tipo_archivo):
        """Solicita credenciales de administrador para regenerar hash"""
        from gui.login_dialog import LoginDialog
        
        login_dialog = LoginDialog(self)
        login_dialog.setWindowTitle("🔐 Autenticación de Administrador - Regenerar Hash")
        login_dialog.header.setText("Se requieren credenciales de administrador para regenerar hash")
        
        if login_dialog.exec():
            username = login_dialog.get_username()
            user_type = login_dialog.get_user_type()
            
            # Verificar que sea administrador
            if username == 'admin' and user_type == 'tecnicos':
                # Obtener nombre completo del usuario
                nombre_completo = self.obtener_nombre_completo_usuario(username)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log(f'[RESTAURACIÓN] Administrador {nombre_completo} ({username}) autenticado para regenerar hash de {tipo_archivo} - {timestamp}')
                return username  # Devolver el nombre del usuario
            else:
                QMessageBox.warning(self, "Acceso Denegado", "Solo el administrador puede regenerar hashes")
                self.log(f'[SECURITY] Intento no autorizado de regenerar hash por {username}')
                return None
        else:
            return False

    def verificar_numero_sesion(self):
        """Verifica la integridad del número de sesión al iniciar"""
        from core.session_manager import leer_numero_sesion
        
        session_number, valid = leer_numero_sesion()
        
        self.log(f'[INFO] Verificando número de sesión: {session_number}, válido: {valid}')
        
        if session_number is None:
            self.log('[INFO] No existe archivo de sesión - creando nueva')
            return True
        
        if not valid:
            # Mostrar modal de discrepancia de sesión
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("⚠️ Discrepancia de Sesión")
            msg_box.setText("Se ha detectado una discrepancia en el número de sesión")
            msg_box.setInformativeText("El contador de sesiones puede haber sido manipulado.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Abort | QMessageBox.StandardButton.Ignore)
            
            res = msg_box.exec()
            
            if res == QMessageBox.StandardButton.Abort:
                return False
        
        # NO incrementar sesión aquí - solo verificar
        return True

    def restaurar_numero_sesion_admin(self):
        """Permite al administrador restaurar el número de sesión"""
        from core.session_manager import restaurar_numero_sesion
        
        # Pedir nuevo número de sesión
        from PyQt6.QtWidgets import QInputDialog
        from PyQt6.QtCore import Qt
        
        text, ok = QInputDialog.getInt(
            self,
            "Restaurar Número de Sesión",
            "Ingrese el número de sesión a restaurar:",
            1,  # valor inicial
            0,   # mínimo
            99999 # máximo
        )
        
        if ok:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if restaurar_numero_sesion(text):
                self.log(f'[RESTAURACIÓN] Número de sesión restaurado a {text} por administrador - {timestamp}')
                self.logger.log_event('SECURITY', f'Sesión restaurada a {text} por administrador', 'warning')
                QMessageBox.information(self, "Éxito", f"Número de sesión restaurado a {text}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo restaurar el número de sesión")
        else:
            self.log('[INFO] Cancelada restauración de número de sesión')

    def setup_console(self):
        """Crea el dock de consola que espera el método log()"""
        self.console_dock = QDockWidget("Consola", self)
        self.console = QTextEdit()  # TIENE QUE LLAMARSE 'console'
        self.console.setReadOnly(True)
        self.console.setFixedHeight(80)
        self.console.setStyleSheet("background-color: #1e1e1e; color: #85e89d; border-top: 1px solid #3e3e42;")
        self.console.clear()
        self.console_dock.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

    def log(self, text):
        # Si el objeto console existe, añade el texto. Si no, solo imprime en terminal.
        if hasattr(self, 'console') and self.console is not None:
            self.console.append(str(text))
        # Eliminado print para reducir DEBUG en consola

    def actualizar_menu_contextual(self, index):
        """Cambia lo que el usuario puede hacer según la pantalla principal"""
        # Si estamos navegando desde próximos, no interferir
        if getattr(self, "_saltando_desde_proximos", False):
            return
            
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # INSTRUMENTOS
            self.log('[SISTEMA] Cambiando a INSTRUMENTOS - limpiando fichas abiertas')
            self.limpiar_ficha_patron()
            if hasattr(self, 'stack'):
                self.stack.setCurrentIndex(0)
            self.current_tipo = 'instrumentos'  # Establecer tipo actual
            self.log('[MODO] Explorando Sección de Instrumentos')
            self.actualizar_arbol_contexto('raiz')
        elif current_tab == 1:  # PATRONES  
            self.log('[SISTEMA] Cambiando a PATRONES - limpiando fichas abiertas')
            self.limpiar_ficha_instrumento()
            if hasattr(self, 'stack_patrones'):
                self.stack_patrones.setCurrentIndex(0)
            self.current_tipo = 'patrones'  # Establecer tipo actual
            self.log('[MODO] Explorando Sección de Patrones')
            self.actualizar_arbol_contexto('raiz')
        elif current_tab == 2:  # CALENDARIO
            self.log('[MODO] Próximas Calibraciones')
            self.actualizar_arbol_contexto('raiz')
    def abrir_gestion_usuarios(self):
        try:
            self.log('[ADMIN] Accediendo al panel de usuarios...')
            dialogo = GestionUsuariosDialog(self)
            result = dialogo.exec()
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def abrir_auditoria_integridad(self):
        """Abre la ventana de Auditoría e Integridad del Sistema"""
        try:
            self.log('[ADMIN] Accediendo al panel de Auditoría e Integridad...')
            dialogo = VentanaAuditoria(self)
            result = dialogo.exec()
            
            # Registrar la acción en el log
            if result == QDialog.Accepted:
                self.logger.log_navigation('Panel Admin', 'Auditoría e Integridad', 'admin')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.log(f'[ERROR] No se pudo abrir la ventana de auditoría: {str(e)}')
    def setup_page_detalle(self):
        """Pantalla de listado de Instrumentos (Nivel 2)"""
        # 1. Layout principal de la página
        layout = QVBoxLayout(self.page_detalle)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # 2. Header (Contenedor horizontal)
        header_layout = QHBoxLayout() # Corregido: antes el descompilador lo llamó 'btn_back'

        # 3. Botón VOLVER
        btn_back = QPushButton('← VOLVER') # Corregido: antes lo llamó 'header'
        btn_back.setObjectName('VolverBtn')
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        # La lógica de volver limpia la ficha y regresa al Dashboard (Index 0)
        btn_back.clicked.connect(lambda: (
            self.limpiar_ficha_instrumento(), 
            self.stack.setCurrentIndex(0), 
            self.actualizar_arbol_contexto('raiz') if hasattr(self, 'actualizar_arbol_contexto') else None
        ))

        # 4. Título de la Familia
        self.lbl_familia_titulo = QLabel('FAMILIA: ---')
        self.lbl_familia_titulo.setStyleSheet('font-size: 18px; color: #2ecc71; font-weight: bold; margin-left: 10px;')

        # 5. Montar el Header
        header_layout.addWidget(btn_back)
        header_layout.addWidget(self.lbl_familia_titulo)
        header_layout.addStretch()

        # 6. Combo de Ordenación
        lbl_orden = QLabel('Ordenar por:')
        lbl_orden.setStyleSheet('color: #888888; font-size: 12px;')
        
        self.combo_orden = QComboBox()
        self.combo_orden.addItems(['Nombre (A-Z)', 'Próxima Calibración'])
        if hasattr(self, 'refresh_tabla_elementos'):
            self.combo_orden.currentTextChanged.connect(self.refresh_tabla_elementos)
        
        header_layout.addWidget(lbl_orden)
        header_layout.addWidget(self.combo_orden)

        # 7. Botón Añadir
        btn_nuevo = QPushButton('+ AÑADIR INSTRUMENTO')
        btn_nuevo.setObjectName('ActionBtn')
        btn_nuevo.setMinimumWidth(180)
        btn_nuevo.clicked.connect(self.abrir_nuevo_elemento)
        
        header_layout.addWidget(btn_nuevo)

        # Añadimos el header completo al layout de la página
        layout.addLayout(header_layout)

        # 8. Área de Scroll para las listas de instrumentos
        self.scroll_elementos = QScrollArea()
        self.scroll_elementos.setWidgetResizable(True)
        self.scroll_elementos.setStyleSheet('border: none; background: transparent;')
        
        self.container_elementos = QWidget()
        self.layout_elementos = QVBoxLayout(self.container_elementos)
        self.layout_elementos.setContentsMargins(0, 0, 5, 0)
        self.layout_elementos.setSpacing(8)
        self.layout_elementos.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_elementos.setWidget(self.container_elementos)
        layout.addWidget(self.scroll_elementos)
        
        # Guardar referencia al layout principal de la página
        self.layout_elementos_principal = layout

    def setup_page_patrones(self):
        """Configura la pestaña de patrones (Bento -> Listado -> Ficha)"""
        layout = QVBoxLayout(self.page_patrones)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack_patrones = QStackedWidget()
        self.page_familias_pat = QWidget()
        layout_fam = QVBoxLayout(self.page_familias_pat)
        btn_add = QPushButton('+ AGREGAR NUEVA FAMILIA DE PATRONES')
        btn_add.setObjectName('ActionBtn')
        btn_add.clicked.connect(lambda: self.crear_familia('patrones'))
        layout_fam.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignLeft)
        self.scroll_pat = QScrollArea()
        self.scroll_pat.setWidgetResizable(True)
        self.scroll_pat.setStyleSheet('border: none; background: transparent;')
        self.bento_container_pat = QWidget()
        self.bento_grid_pat = QGridLayout(self.bento_container_pat)
        self.scroll_pat.setWidget(self.bento_container_pat)
        layout_fam.addWidget(self.scroll_pat)
        self.page_lista_patrones = QWidget()
        layout_lista = QVBoxLayout(self.page_lista_patrones)
        layout_lista.setContentsMargins(15, 10, 15, 10)
        header_pat = QHBoxLayout()
        btn_back_pat = QPushButton('← VOLVER')
        btn_back_pat.setObjectName('VolverBtn')
        btn_back_pat.clicked.connect(lambda: (self.limpiar_ficha_patron(), self.stack_patrones.setCurrentIndex(0), self.actualizar_arbol_contexto('raiz')))
        self.lbl_patrones_titulo = QLabel('FAMILIA: PATRONES')
        self.lbl_patrones_titulo.setStyleSheet('font-size: 18px; color: #569cd6; font-weight: bold; margin-left: 10px;')
        header_pat.addWidget(btn_back_pat)
        header_pat.addWidget(self.lbl_patrones_titulo)
        header_pat.addStretch()
        lbl_orden_pat = QLabel('Ordenar por:')
        lbl_orden_pat.setStyleSheet('color: #888888; font-size: 12px;')
        self.combo_orden_pat = QComboBox()
        self.combo_orden_pat.addItems(['Nombre (A-Z)', 'Próxima Calibración'])
        self.combo_orden_pat.currentTextChanged.connect(self.refresh_lista_patrones)
        header_pat.addWidget(lbl_orden_pat)
        header_pat.addWidget(self.combo_orden_pat)
        btn_nuevo_pat = QPushButton('+ NUEVO PATRÓN')
        btn_nuevo_pat.setObjectName('ActionBtn')
        btn_nuevo_pat.setMinimumWidth(180)
        btn_nuevo_pat.clicked.connect(self.abrir_nuevo_elemento)
        header_pat.addWidget(btn_nuevo_pat)
        layout_lista.addLayout(header_pat)
        self.scroll_lista_patrones = QScrollArea()
        self.scroll_lista_patrones.setWidgetResizable(True)
        self.scroll_lista_patrones.setStyleSheet('border: none; background: transparent;')
        self.container_lista_patrones = QWidget()
        self.layout_lista_patrones = QVBoxLayout(self.container_lista_patrones)
        self.layout_lista_patrones.setContentsMargins(0, 0, 5, 0)
        self.layout_lista_patrones.setSpacing(8)
        self.layout_lista_patrones.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_lista_patrones.setWidget(self.container_lista_patrones)
        layout_lista.addWidget(self.scroll_lista_patrones)
        self.page_ficha_patron = QWidget()
        self.layout_ficha_patron = QVBoxLayout(self.page_ficha_patron)
        self.stack_patrones.addWidget(self.page_familias_pat)
        self.stack_patrones.addWidget(self.page_lista_patrones)
        self.stack_patrones.addWidget(self.page_ficha_patron)
        layout.addWidget(self.stack_patrones)
        
    def setup_page_proximos(self):
        """Configura la pestaña de próximas calibraciones con filtros"""
        # Limpiar layout anterior si existe
        layout_old = self.page_proximos.layout()
        if layout_old:
            while layout_old.count():
                child = layout_old.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        else:
            layout = QVBoxLayout(self.page_proximos)
            
        layout = self.page_proximos.layout()
        layout.setContentsMargins(20, 20, 20, 20)
        header_layout = QHBoxLayout()
        title = QLabel('PRÓXIMAS CADUCIDADES')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #569cd6;')
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.filter_group = QButtonGroup(self)
        filter_layout = QHBoxLayout()
        filters = [('TODOS', 'all'), ('PATRONES', 'patrones'), ('INSTRUMENTOS', 'instrumentos')]
        for text, filter_id in filters:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty('filter_id', filter_id)
            btn.setStyleSheet('\n                QPushButton {\n                    background-color: #252526; border: 1px solid #454545; color: #cccccc;\n                    padding: 6px 15px; border-radius: 4px; font-weight: bold;\n                }\n                QPushButton:checked {\n                    background-color: #007acc; color: white; border: 1px solid #007acc;\n                }\n                QPushButton:hover { background-color: #3e3e42; }\n            ')
            if filter_id == 'all':
                btn.setChecked(True)
            self.filter_group.addButton(btn)
            filter_layout.addWidget(btn)
        self.filter_group.buttonClicked.connect(self.actualizar_tabla_proximos)
        header_layout.addLayout(filter_layout)
        layout.addLayout(header_layout)
        self.tabla_proximos = QTableWidget()
        self.tabla_proximos.setColumnCount(5)
        self.tabla_proximos.setHorizontalHeaderLabels(['ID', 'DESCRIPCIÓN', 'FAMILIA', 'VENCIMIENTO', 'ESTADO'])
        self.tabla_proximos.setStyleSheet('\n            QTableWidget {\n                background-color: #1e1e1e; color: #d4d4d4; gridline-color: #333333;\n                border: 1px solid #333333; font-size: 13px;\n            }\n            QHeaderView::section {\n                background-color: #2d2d2d; color: #569cd6; padding: 5px; font-weight: bold; border: 1px solid #333333;\n            }\n        ')
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_proximos.itemClicked.connect(self.ir_a_ficha_desde_proximos)
        self.tabla_proximos.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.tabla_proximos)
        self.actualizar_tabla_proximos()

    def setup_page_ficha_tecnica(self):
        """Pantalla de detalle del Instrumento/Patrón (Nivel 3)"""
        # 1. Layout Principal
        layout = QVBoxLayout(self.page_ficha_tecnica)
        layout.setContentsMargins(15, 10, 15, 5)
        layout.setSpacing(5)

        # 2. Header (Corregido: btn_back es el botón y header_layout el contenedor)
        header_layout = QHBoxLayout()
        
        btn_back = QPushButton('← VOLVER A LISTADO')
        btn_back.setObjectName('VolverBtn')
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        # Al volver, vamos al Nivel 2 (Index 1 del stack)
        btn_back.clicked.connect(lambda: (
            self.limpiar_ficha_instrumento(), 
            self.stack.setCurrentIndex(1), 
            self.refresh_tabla_elementos(),
            self.actualizar_arbol_contexto('familia') if hasattr(self, 'actualizar_arbol_contexto') else None
        ))

        self.lbl_id_elemento = QLabel('ID: ---')
        self.lbl_id_elemento.setStyleSheet('font-weight: bold; font-size: 18px; color: #ffffff; margin-left: 20px;')

        btn_upload = QPushButton('SUBIR ARCHIVOS')
        btn_upload.setObjectName('ActionBtn')
        btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upload.clicked.connect(self.subir_archivos)

        header_layout.addWidget(btn_back)
        header_layout.addWidget(self.lbl_id_elemento)
        header_layout.addStretch()
        header_layout.addWidget(btn_upload)
        layout.addLayout(header_layout)

        # 3. Cuerpo Central (Dos columnas)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(25)

        # --- COLUMNA IZQUIERDA: Datos y Calibraciones ---
        col_izq = QVBoxLayout()
        col_izq.setSpacing(10)

        lbl_info = QLabel('DATOS TÉCNICOS')
        lbl_info.setFixedHeight(25)
        lbl_info.setStyleSheet('color: #569cd6; font-weight: bold; font-size: 13px;')
        col_izq.addWidget(lbl_info)

        self.info_txt = QTextEdit()
        self.info_txt.setReadOnly(True)
        self.info_txt.setStyleSheet('''
            QTextEdit {
                background-color: #252526; 
                color: #d4d4d4; 
                font-size: 13px; 
                padding: 10px; 
                border: 1px solid #3e3e42; 
                border-radius: 4px;
            }
        ''')
        col_izq.addWidget(self.info_txt, 3) # Prioridad de tamaño 3

        lbl_calib = QLabel('HISTORIAL DE CALIBRACIONES')
        lbl_calib.setFixedHeight(25)
        lbl_calib.setStyleSheet('color: #569cd6; font-weight: bold; font-size: 13px;')
        col_izq.addWidget(lbl_calib)

        self.tabla_calibraciones = QTableWidget()
        self.tabla_calibraciones.setColumnCount(3)
        self.tabla_calibraciones.setHorizontalHeaderLabels(['Fecha', 'Responsable', 'Estado'])
        self.tabla_calibraciones.verticalHeader().setVisible(False)
        self.tabla_calibraciones.horizontalHeader().setStretchLastSection(True)
        self.tabla_calibraciones.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_calibraciones.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Conexiones de la tabla
        self.tabla_calibraciones.itemSelectionChanged.connect(self.actualizar_tabla_puntos)
        
        col_izq.addWidget(self.tabla_calibraciones, 2) # Prioridad de tamaño 2

        # --- COLUMNA DERECHA: Gráfica y Puntos ---
        col_der = QVBoxLayout()
        col_der.setSpacing(10)

        lbl_grafica = QLabel('GRÁFICA METROLÓGICA')
        lbl_grafica.setFixedHeight(25)
        lbl_grafica.setStyleSheet('color: #569cd6; font-weight: bold; font-size: 13px;')
        col_der.addWidget(lbl_grafica)

        self.grafica_container = QFrame()
        self.grafica_container.setStyleSheet('background-color: #252526; border: 1px solid #3e3e42; border-radius: 4px;')
        self.grafica_container.setMinimumHeight(290)
        self.grafica_layout = QVBoxLayout(self.grafica_container)
        col_der.addWidget(self.grafica_container, 3)

        self.btn_ver_puntos = QPushButton('📊 VER DETALLES DE LECTURAS (Puntos de Control)')
        self.btn_ver_puntos.setStyleSheet('''
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #0078d4;
                border-radius: 4px;
                color: #0078d4;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                margin: 5px;
            }
            QPushButton:hover { background-color: #0078d4; color: white; }
        ''')
        self.btn_ver_puntos.clicked.connect(self.abrir_modal_puntos)
        col_der.addWidget(self.btn_ver_puntos)

        cuerpo.addLayout(col_izq, 1)
        cuerpo.addLayout(col_der, 2)
        layout.addLayout(cuerpo)

        # 4. Footer (Acciones rápidas)
        self.contenedor_footer = QFrame()
        footer_layout = QHBoxLayout(self.contenedor_footer)
        footer_layout.setContentsMargins(0, 5, 0, 5)
        footer_layout.addStretch()

        # Botones del Footer
        self.btn_pdf_ficha = QPushButton('GENERAR PDF INFORME')
        self.btn_pdf_ficha.setFixedSize(200, 32)
        self.btn_pdf_ficha.clicked.connect(self.generar_pdf_actual)
        footer_layout.addWidget(self.btn_pdf_ficha)

        self.btn_nueva_cal_ficha = QPushButton('NUEVA CALIBRACIÓN')
        self.btn_nueva_cal_ficha.setObjectName('ActionBtn')
        self.btn_nueva_cal_ficha.setFixedSize(200, 32)
        self.btn_nueva_cal_ficha.clicked.connect(self.lanzar_calibracion)
        footer_layout.addWidget(self.btn_nueva_cal_ficha)

        self.btn_estado_dinamico = QPushButton('ESTADO')
        self.btn_estado_dinamico.setObjectName('ActionBtn')
        self.btn_estado_dinamico.setFixedSize(180, 32)
        footer_layout.addWidget(self.btn_estado_dinamico)

        self.btn_borrar_ficha = QPushButton('ELIMINAR')
        self.btn_borrar_ficha.setFixedSize(120, 32)
        self.btn_borrar_ficha.setStyleSheet('background-color: #c0392b; color: white; font-weight: bold; border-radius: 4px;')
        # Conectamos a tu función de borrado físico
        self.btn_borrar_ficha.clicked.connect(lambda: self.borrar_elemento_fisico(self.lbl_id_elemento.text().replace("ID: ", ""), getattr(self, 'current_tipo', 'instrumentos')))
        
        footer_layout.addWidget(self.btn_borrar_ficha)
        layout.addWidget(self.contenedor_footer)

    def abrir_modal_puntos(self):
        selected_rows = self.tabla_calibraciones.selectedItems()
        row = self.tabla_calibraciones.currentRow()
        
        if not selected_rows:
            # Si no hay filas seleccionadas, usar la fila actual
            pass
        else:
            # Si hay filas seleccionadas, usar la primera
            row = self.tabla_calibraciones.row(selected_rows[0])
        
        idx = len(self.historial_actual) - 1 - row
        puntos = self.historial_actual[idx].get('puntos', []) if 0 <= idx < len(self.historial_actual) else self.historial_actual[idx].get('puntos', [])
        calibracion_info = self.historial_actual[idx]
        
        dialogo = VentanaPuntos(puntos, calibracion_info, parent=self)
        dialogo.exec()

    def lanzar_calibracion(self):
        """Abre la ventana de calibración dinámica - Solo para técnicos"""
        # ***<module>.MetrologiaApp.lanzar_calibracion: Failure: Compilation Error
        if not self.current_user:
            login_dialog = LoginDialog(self)
            if login_dialog.exec() is None:
                self.current_user = login_dialog.get_username()
                self.user_type = login_dialog.get_user_type()
                self.logger.set_user(self.current_user)
                self.log(f'[SISTEMA] Usuario autenticado: {self.current_user} ({self.user_type})')
            else:
                QMessageBox.warning(self, 'Acceso Denegado', 'Debe iniciar sesión para realizar una calibración.')
            self.log(f'[SISTEMA] Acceso denegado: {self.current_user} no es técnico') if self.user_type!= 'tecnicos' else None
            QMessageBox.warning(self, 'Acceso Denegado', 'Solo los técnicos pueden realizar calibraciones.')
        else:
            self.log(f'[SISTEMA] Iniciando protocolo de calibración para: {self.current_elemento_id}')
            self.logger.log_calibration(self.current_elemento_id, self.current_familia, self.current_user)
            from gui.calibration_window import CalibrationWindow
            self.win_cal = CalibrationWindow(self.current_elemento_id, self.current_familia, self.log, self.current_user_data)
            self.win_cal.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.win_cal.show()
    def modal_actualizar_patron(self, data_json, path_json):
        # ***<module>.MetrologiaApp.modal_actualizar_patron: Failure: Different bytecode
        from PyQt6.QtWidgets import QDateEdit, QFileDialog
        from PyQt6.QtCore import QDate
        import shutil
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Nueva Calibración: {self.current_elemento_id}')
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('<b>Fecha de Calibración:</b>'))
        f_input = QDateEdit()
        f_input.setCalendarPopup(True)
        f_input.setDate(QDate.currentDate())
        layout.addWidget(f_input)
        layout.addWidget(QLabel('<b>Laboratorio / Entidad:</b>'))
        lab_input = QTextEdit()
        lab_input.setFixedHeight(30)
        layout.addWidget(lab_input)
        layout.addWidget(QLabel('<b>Incertidumbre declarada (k=2):</b>'))
        inc_input = QTextEdit()
        inc_input.setFixedHeight(30)
        layout.addWidget(inc_input)
        path_pdf = ['']
        lbl_pdf = QLabel('Certificado no seleccionado')
        btn_pdf = QPushButton('Adjuntar Certificado')
        btn_pdf.setStyleSheet('background-color: #0e639c; color: white; font-weight: bold;')
        def get_pdf():
            # ***<module>.MetrologiaApp.modal_actualizar_patron.get_pdf: Failure: Different bytecode
            f, _ = QFileDialog.getOpenFileName(dialog, 'Seleccionar PDF', '', 'PDF Files (*.pdf)')
            if f:
                path_pdf[0] = f
        btn_pdf.clicked.connect(get_pdf)
        layout.addWidget(btn_pdf)
        layout.addWidget(lbl_pdf)
        btn_save = QPushButton('REGISTRAR Y CERRAR')
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet('\n                            QPushButton {\n                                background-color: #1a1a1a;\n                                border: 1px solid #0078d4;\n                                border-radius: 4px;\n                                color: #0078d4;\n                                padding: 12px;\n                                font-weight: bold;\n                                font-size: 14px;\n                                margin: 5px;\n                            }\n                            QPushButton:hover {\n                                background-color: #0078d4;\n                                color: white;\n                            }\n                            QPushButton:pressed {\n                                background-color: #005a9e;\n                            }\n                        ')
        layout.addWidget(btn_save)
        def guardar():
            # Validar campos obligatorios
            if not lab_input.toPlainText() or not inc_input.toPlainText():
                QMessageBox.warning(dialog, 'Aviso', 'Rellena laboratorio e incertidumbre')
                return
                
            # Crear carpeta de documentos si es necesario
            if path_pdf[0]:
                folder_docs = os.path.join(os.path.dirname(path_json), 'documentos')
                os.makedirs(folder_docs, exist_ok=True)
                
            # Crear nueva entrada
            nueva_entrada = {
                'fecha_calibracion': f_input.date().toString('yyyy-MM-dd'),
                'laboratorio': lab_input.toPlainText(),
                'incertidumbre': inc_input.toPlainText(),
                'usuario_tecnico': self.current_user,
                'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'certificado': os.path.basename(path_pdf[0]) if path_pdf[0] else ''
            }
            
            if 'historial' not in data_json:
                data_json['historial'] = []
                
            data_json['historial'].append(nueva_entrada)
            data_json['fecha_ultima_calibracion'] = nueva_entrada['fecha_calibracion']
            data_json['incertidumbre'] = nueva_entrada['incertidumbre']
            
            if guardar_json_con_hash(path_json, data_json, elemento_id):
                self.log(f'[HASH] Hash actualizado para {elemento_id} tras actualizar calibración')
            else:
                self.log(f'[ERROR] No se pudo actualizar hash para {elemento_id}')
                
            self.log(f'[METROLOGÍA] Calibración actualizada por {nueva_entrada["usuario_tecnico"]}')
            dialog.accept()
            
        btn_save.clicked.connect(guardar)
        dialog.exec()
    def marcar_obsoleto(self):
        """Marca el elemento actual como obsoleto (Instrumento o Patrón) - Solo para técnicos"""
        # ***<module>.MetrologiaApp.marcar_obsoleto: Failure: Different bytecode
        if not self.current_user:
            d = LoginDialog(self)
            if d.exec() is None:
                self.current_user = d.get_username()
                self.user_type = d.get_user_type()
                self.logger.set_user(self.current_user)
            else:
                return None
        if self.user_type!= 'tecnicos':
            QMessageBox.warning(self, 'Acceso Denegado', 'Solo los técnicos pueden marcar elementos como obsoletos.')
        else:
            if not hasattr(self, 'current_elemento_id'):
                QMessageBox.warning(self, 'Error', 'No hay ningún elemento seleccionado.')
            else:
                reply = QMessageBox.question(self, 'Confirmar', f'¿Está seguro que desea marcar el elemento {self.current_elemento_id} como OBSOLETO?\n\nEsta acción se puede revertir.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        tipo_folder = getattr(self, 'current_tipo', 'instrumentos')
                        path = get_data_path(os.path.join('data', tipo_folder, self.current_familia, self.current_elemento_id, f'{self.current_elemento_id}.json'))
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            data = json.load(f)
                        data['estado'] = 'obsoleto'
                        
                        if guardar_json_con_hash(path, data, self.current_elemento_id):
                            self.log(f'[HASH] Hash actualizado para {self.current_elemento_id} tras marcar como obsoleto')
                        else:
                            self.log(f'[ERROR] No se pudo actualizar hash para {self.current_elemento_id}')
                        
                        self.logger.log_event('RETIREMENT', f'{tipo_folder.upper()} {self.current_elemento_id} marcado como OBSOLETO por {self.current_user}', 'warning')
                        self.log(f'[INFO] {tipo_folder} {self.current_elemento_id} marcado como OBSOLETO')
                        QMessageBox.information(self, 'Éxito', 'Elemento marcado como OBSOLETO')
                        from indices import generar_indices
                        generar_indices()
                        if tipo_folder == 'patrones':
                            self.cargar_ficha_patron(self.current_elemento_id)
                        else:
                            self.cargar_ficha_elemento(self.current_elemento_id)
                        self.refresh_tabla_elementos()
                    except Exception as e:
                        self.log(f'[ERROR] No se pudo marcar como obsoleto: {e}')
                        QMessageBox.critical(self, 'Error', f'No se pudo actualizar el estado: {e}')
    def marcar_apto(self):
        """Marca el elemento actual como apto (quita obsoleto) - Solo para técnicos"""
        # ***<module>.MetrologiaApp.marcar_apto: Failure: Different bytecode
        if not self.current_user:
            d = LoginDialog(self)
            if d.exec() is None:
                self.current_user = d.get_username()
                self.user_type = d.get_user_type()
                self.logger.set_user(self.current_user)
            else:
                return None
        if self.user_type!= 'tecnicos':
            QMessageBox.warning(self, 'Acceso Denegado', 'Solo los técnicos pueden marcar elementos como aptos.')
        else:
            if not hasattr(self, 'current_elemento_id'):
                QMessageBox.warning(self, 'Error', 'No hay ningún elemento seleccionado.')
            else:
                reply = QMessageBox.question(self, 'Confirmar', f'¿Está seguro que desea marcar el elemento {self.current_elemento_id} como APTO?\n\nVolverá a aparecer en los listados.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        tipo_folder = getattr(self, 'current_tipo', 'instrumentos')
                        path = get_data_path(os.path.join('data', tipo_folder, self.current_familia, self.current_elemento_id, f'{self.current_elemento_id}.json'))
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            data = json.load(f)
                        if 'estado' in data:
                            del data['estado']
                        
                        if guardar_json_con_hash(path, data, self.current_elemento_id):
                            self.log(f'[HASH] Hash actualizado para {self.current_elemento_id} tras marcar como apto')
                        else:
                            self.log(f'[ERROR] No se pudo actualizar hash para {self.current_elemento_id}')
                        
                        self.logger.log_event('RESTORE', f'{tipo_folder.upper()} {self.current_elemento_id} reactivado como APTO por {self.current_user}', 'success')
                        self.log(f'[INFO] {tipo_folder} {self.current_elemento_id} restaurado como APTO')
                        QMessageBox.information(self, 'Éxito', 'Elemento marcado como APTO')
                        from indices import generar_indices
                        generar_indices()
                        if tipo_folder == 'patrones':
                            self.cargar_ficha_patron(self.current_elemento_id)
                        else:
                            self.cargar_ficha_elemento(self.current_elemento_id)
                        self.refresh_tabla_elementos()
                    except Exception as e:
                        self.log(f'[ERROR] No se pudo marcar como apto: {e}')
                        QMessageBox.critical(self, 'Error', f'No se pudo actualizar el estado: {e}')
    def generar_pdf_actual(self):
        """Genera PDF con la calibración seleccionada en la tabla"""
        if not hasattr(self, 'current_elemento_id'):
            self.log('[ERROR] No hay ningún elemento seleccionado para generar el PDF.')
            return
        
        # Obtener la calibración seleccionada
        fila_visual = self.tabla_calibraciones.currentRow()
        if fila_visual < 0:
            self.log('[ERROR] No hay ninguna calibración seleccionada.')
            return
        
        indice_real = len(self.historial_actual) - 1 - fila_visual
        if indice_real < 0 or indice_real >= len(self.historial_actual):
            self.log('[ERROR] Índice de calibración inválido.')
            return
        
        # Cargar datos completos del elemento
        path_json = get_data_path(os.path.join('data/instrumentos', self.current_familia, self.current_elemento_id, f'{self.current_elemento_id}.json'))
        
        try:
            with open(path_json, 'r', encoding='utf-8', errors='ignore') as f:
                data_completo = json.load(f)
            
            # Extraer solo la calibración seleccionada
            calibracion_seleccionada = self.historial_actual[indice_real]
            
            # Crear estructura de datos solo para la calibración seleccionada
            datos_pdf = {
                'id': data_completo.get('id', 'N/A'),
                'descripcion': data_completo.get('descripcion', 'N/A'),
                'rango_min': data_completo.get('rango_min', 'N/A'),
                'rango_max': data_completo.get('rango_max', 'N/A'),
                'periodicidad_meses': data_completo.get('periodicidad_meses', 'N/A'),
                'patrones_sugeridos': data_completo.get('patrones_sugeridos', 'N/A'),
                'historial': [calibracion_seleccionada]  # SOLO la calibración seleccionada
            }
            
            # Generar PDF específico con fecha en el nombre
            fecha_cal = calibracion_seleccionada.get('fecha_calibracion', '').split()[0].replace('-', '')
            ruta_pdf = get_data_path(os.path.join('data/instrumentos', self.current_familia, self.current_elemento_id, f'ICI_{self.current_elemento_id}_{fecha_cal}.pdf'))
            
            from core.pdf_generator import exportar_a_pdf
            exportar_a_pdf(datos_pdf, ruta_pdf)
            
            # --- REGISTRO DE IMPRESIÓN EN LOG ---
            elemento_id = datos_pdf.get('id', 'N/A')
            fecha_calibracion = calibracion_seleccionada.get('fecha_calibracion', 'N/A')
            
            # Generar ID del informe para el log
            if fecha_calibracion != 'N/A':
                try:
                    fecha_iso = fecha_calibracion.split()[0]  # YYYY-MM-DD
                    id_informe = f"ICI-{elemento_id}-{fecha_iso.replace('-', '')}"
                except:
                    from datetime import datetime
                    id_informe = f"ICI-{elemento_id}-{datetime.now().strftime('%Y%m%d')}"
                    fecha_iso = datetime.now().strftime('%Y-%m-%d')
            else:
                from datetime import datetime
                id_informe = f"ICI-{elemento_id}-{datetime.now().strftime('%Y%m%d')}"
                fecha_iso = datetime.now().strftime('%Y-%m-%d')
            
            # Usar el logger del sistema para guardar en metrologia_log.json
            from core.logger import get_logger
            logger = get_logger()
            logger.log_event("DATA", f"ICI generado: {id_informe} para {elemento_id}. Fecha calibración: {fecha_iso}")
            
            QMessageBox.information(self, 'Éxito', 'Informe generado para la calibración seleccionada.')
            
        except Exception as e:
            self.log(f'[ERROR] No se pudo generar el PDF: {e}')

    def cargar_ficha_elemento(self, id_elemento):
        self.current_elemento_id = id_elemento
        self.current_tipo = 'instrumentos'
        path = get_data_path(os.path.join('data', 'instrumentos', self.current_familia, id_elemento, f'{id_elemento}.json'))
        self.log(f'[MODO] Explorando ficha instrumento {id_elemento}')
        
        if not os.path.exists(path):
            self.log(f'[ERROR] No existe el archivo: {path}')
            return
        
        # Verificar integridad del archivo usando función unificada
        if not self.verificar_integridad_elemento(path, id_elemento, 'elemento'):
            return
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        self.lbl_id_elemento.setText(f'ID: {data['id']}')
        r_min = data.get('rango_min', 'N/A')
        r_max = data.get('rango_max', 'N/A')
        try:
            self._current_rango_min = float(r_min) if isinstance(r_min, (int, float, str)) and r_min!= 'N/A' else 0
            self._current_rango_max = float(r_max) if isinstance(r_max, (int, float, str)) and r_max!= 'N/A' else 25
        except (ValueError, TypeError):
            self._current_rango_min = 0
            self._current_rango_max = 25
        incertidumbre_total_str = '0.0000'
        res = data.get('resolucion', '0.0001')
        historial = data.get('historial', [])
        if historial:
            ultima_calib = historial[(-1)]
            puntos = ultima_calib.get('puntos', [])
            if puntos:
                try:
                    valores_totales = []
                    for p in puntos:
                        error = abs(float(p.get('error', 0)))
                        inc_k2 = float(p.get('incertidumbre_k2', 0))
                        valores_totales.append(error + inc_k2)
                    max_total = max(valores_totales)
                    incertidumbre_total_str = f'{max_total:.4f}'
                except (ValueError, TypeError):
                    incertidumbre_total_str = '0.0000'
                else:
                    pass
        else:
            inc_base = data.get('incertidumbre_elemento', 0)
            incertidumbre_total_str = f'{float(inc_base):.4f}'
        proxima_dt, ultima_calib = self.calcular_proxima_calibracion(data)
        proxima_calib = proxima_dt.strftime('%Y-%m-%d') if proxima_dt else 'N/A'
        if ultima_calib is None:
            ultima_calib = 'N/A'
        estado_elemento = self.obtener_estado_calibracion(data)
        clase_estado = 'estado-obsoleto'
        if estado_elemento == 'APTO':
            clase_estado = 'estado-apto'
        else:
            if estado_elemento == 'NO APTO':
                clase_estado = 'estado-no-apto'
        texto_info = f'''\n                <style>\n                    body {{ font-family: 'Segoe UI', Arial; color: #d4d4d4; }}\n                    .label {{ font-weight: bold; color: #3498db; }}\n                    .valor {{ color: #ffffff; }}\n                    .linea {{ margin: 8px 0; }}\n                    .estado-apto {{ color: #2ecc71; font-weight: bold; }}\n                    .estado-no-apto {{ color: #e74c3c; font-weight: bold; }}\n                    .estado-obsoleto {{ color: #f39c12; font-weight: bold; }}\n                </style>\n                <div class="linea"><span class="label">Descripción:</span> <span class="valor">{data.get('descripcion', 'N/A')}</span></div>\n                <div class="linea"><span class="label">Rango de Medida:</span> <span class="valor">{r_min} a {r_max} mm</span></div>\n                <div class="linea"><span class="label">Incertidumbre Total (|E|+U):</span> <span class="valor">{incertidumbre_total_str} mm</span></div>\n                <div class="linea"><span class="label">Resolución:</span> <span class="valor">{res} mm</span></div>\n                <div class="linea"><span class="label">Periodicidad:</span> <span class="valor">{data.get('periodicidad_meses', 12)} meses</span></div>\n                <div class="linea"><span class="label">Patrones:</span> <span class="valor">{data.get('patrones_sugeridos', 'N/A')}</span></div>\n                <div class="linea"><span class="label">ESTADO:</span> <span class="{clase_estado}">{estado_elemento}</span></div>\n                <div class="linea"><span class="label">Última Calibración:</span> <span class="valor">{ultima_calib}</span></div>\n                <div class="linea"><span class="label">Próxima Calibración:</span> <span class="valor">{proxima_calib}</span></div>\n                '''
        self.info_txt.setHtml(texto_info)
        self.historial_actual = data.get('historial', [])
        historial = self.historial_actual
        self.tabla_calibraciones.setRowCount(len(historial))
        from PyQt6.QtWidgets import QTableWidgetItem
        from PyQt6.QtGui import QColor
        for row, calibracion in enumerate(reversed(historial)):
            fecha = calibracion.get('fecha_calibracion', 'N/A')
            responsable = calibracion.get('responsable', 'N/A')
            apto_calibracion = 'APTO' if calibracion.get('apto', False) else 'NO APTO'
            item_fecha = QTableWidgetItem(str(fecha))
            item_responsable = QTableWidgetItem(str(responsable))
            item_estado = QTableWidgetItem(apto_calibracion)
            color = QColor('#2ecc71') if apto_calibracion == 'APTO' else QColor('#e74c3c')
            item_estado.setForeground(color)
            self.tabla_calibraciones.setItem(row, 0, item_fecha)
            self.tabla_calibraciones.setItem(row, 1, item_responsable)
            self.tabla_calibraciones.setItem(row, 2, item_estado)
        # Limpiar widgets anteriores del layout
        if len(historial) > 0:
            self.tabla_calibraciones.selectRow(0)
        
        while self.grafica_layout.count():
            item = self.grafica_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        from core.grafica_generator import crear_grafica_metrologia
        canvas = crear_grafica_metrologia(data)
        canvas.mousePressEvent = lambda event: self.abrir_grafica_detallada(event, canvas)
        self.grafica_layout.addWidget(canvas)
        
        rol = str(self.user_type).lower().strip()
        estado_actual = data.get('estado', '').lower()
        
        if estado_actual == 'obsoleto':
            self.btn_estado_dinamico.setText('MARCAR COMO APTO')
            self.btn_estado_dinamico.setStyleSheet('background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px;')
            self.btn_estado_dinamico.clicked.connect(self.marcar_apto)
        else:
            self.btn_estado_dinamico.setText('MARCAR COMO OBSOLETO')
            self.btn_estado_dinamico.setStyleSheet('background-color: #f39c12; color: white; font-weight: bold; border-radius: 4px;')
            self.btn_estado_dinamico.clicked.connect(self.marcar_obsoleto)
            
        es_tecnico = rol in ('admin', 'tecnicos')
        self.btn_nueva_cal_ficha.setVisible(es_tecnico)
        self.btn_estado_dinamico.setVisible(es_tecnico)
        self.btn_borrar_ficha.setVisible(str(self.current_user).strip() == 'admin')
        self.btn_borrar_ficha.clicked.connect(lambda: self.borrar_elemento_fisico(id_elemento, 'instrumentos'))
        self.stack.setCurrentIndex(2)
        self.actualizar_arbol_contexto('elemento')

    def cargar_ficha_patron(self, id_patron):
        # irreducible cflow, using cdg fallback
        """\nCarga la ficha técnica del patrón replicando la estructura de Navbar \ny estilos de botones de la ficha de instrumentos.\n"""
        # ***<module>.MetrologiaApp.cargar_ficha_patron: Failure: Compilation Error
        base_patrones = get_data_path(os.path.join('data', 'patrones'))
        encontrado = False
        ruta_elemento = ''
        nombre_usuario = str(self.current_user).strip()
        # Buscar el patrón en todas las familias
        if os.path.exists(base_patrones):
            for familia in os.listdir(base_patrones):
                posible_ruta = os.path.join(base_patrones, familia, id_patron)
                if os.path.exists(posible_ruta) and os.path.exists(os.path.join(posible_ruta, f'{id_patron}.json')):
                    self.current_familia = familia
                    ruta_elemento = posible_ruta
                    encontrado = True
                    break
        if not encontrado:
            return None
        else:
            self.current_elemento_id = id_patron
            self.log(f'[MODO] Explorando ficha patrón: {id_patron}')
            self.current_tipo = 'patrones'
            path_json = os.path.join(ruta_elemento, f'{id_patron}.json')
        
        # Verificar integridad del archivo usando función unificada
        if not self.verificar_integridad_elemento(path_json, id_patron, 'patron'):
            return None
        
        try:
            with open(path_json, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            proxima_calib, _ = self.calcular_proxima_calibracion(data)
            proxima_calib_str = proxima_calib.strftime('%Y-%m-%d') if proxima_calib else 'N/A'
            
            # Limpiar layout anterior
            while self.layout_ficha_patron.count():
                item = self.layout_ficha_patron.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            navbar = QHBoxLayout()
            btn_volver = QPushButton('← VOLVER AL LISTADO')
            btn_volver.setMinimumHeight(35)
            btn_volver.setObjectName('ActionBtn')
            btn_volver.clicked.connect(lambda: (self.limpiar_ficha_patron(), self.stack_patrones.setCurrentIndex(1), self.refresh_lista_patrones(), self.actualizar_arbol_contexto('familia')))
            navbar.addWidget(btn_volver)
            navbar.addStretch()
            self.layout_ficha_patron.addLayout(navbar)
            lbl_id = QLabel(f'ID PATRÓN: {id_patron}')
            lbl_id.setStyleSheet('font-size: 18px; font-weight: bold; color: #ffffff; margin-top: 10px; margin-bottom: 5px;')
            self.layout_ficha_patron.addWidget(lbl_id)
            info_patron = QTextEdit()
            info_patron.setReadOnly(True)
            info_patron.setFrameStyle(0)
            info_patron.setStyleSheet('background-color: transparent;')
            texto_html = f'''
            <style>
                body {{ font-family: 'Segoe UI', Arial; color: #d4d4d4; }}
                .label {{ font-weight: bold; color: #3498db; }}
                .valor {{ color: #ffffff; }}
                .linea {{ margin: 6px 0; }}
                hr {{ border: 0; border-top: 1px solid #3e3e42; margin: 15px 0; }}
            </style>
            <div class="linea"><span class="label">Descripción:</span> <span class="valor">{data.get('descripcion', 'N/A')}</span></div>
            <div class="linea"><span class="label">Familia:</span> <span class="valor">{self.current_familia}</span></div>
            <div class="linea"><span class="label">Valor Nominal:</span> <span class="valor">{data.get('valor_nominal', 'N/A')} mm</span></div>
            <div class="linea"><span class="label">Incertidumbre (k=2):</span> <span class="valor">{data.get('incertidumbre', 'N/A')}</span></div>
            <div class="linea"><span class="label">Periodicidad:</span> <span class="valor">{data.get('periodicidad_meses', 'N/A')} meses</span></div>
            <div class="linea"><span class="label">Fecha Última Calibración:</span> <span class="valor">{data.get('fecha_ultima_calibracion', 'N/A')}</span></div>
            <div class="linea"><span class="label">Fecha Próxima Calibración:</span> <span class="valor">{proxima_calib_str}</span></div>
            <hr>
            <div style="color: #3498db; font-weight: bold; margin-bottom: 10px;">DOCUMENTOS DISPONIBLES EN SISTEMA:</div>
            '''
            info_patron.setHtml(texto_html)
            info_patron.setFixedHeight(240)
            self.layout_ficha_patron.addWidget(info_patron)
            style_botones_archivos = '\n                        QPushButton {\n                            background-color: #333333;\n                            border: 1px solid #444444;\n                            border-radius: 4px;\n                            color: #cccccc;\n                            text-align: left;\n                            padding: 12px;\n                            font-weight: normal;\n                            margin-bottom: 4px;\n                        }\n                        QPushButton:hover {\n                            background-color: #3e3e42;\n                            border: 1px solid #0e639c;\n                            color: #ffffff;\n                        }\n                    '
            ruta_docs = os.path.join(ruta_elemento, 'documentos')
            if os.path.exists(ruta_docs):
                for archivo in os.listdir(ruta_docs):
                    btn_file = QPushButton(f'  {archivo}')
                    btn_file.setStyleSheet(style_botones_archivos)
                    btn_file.clicked.connect(lambda ch, p=os.path.join(ruta_docs, archivo): os.startfile(p))
                    self.layout_ficha_patron.addWidget(btn_file)
            layout_acciones = QHBoxLayout()
            layout_acciones.setContentsMargins(0, 20, 0, 10)
            rol = str(self.user_type).lower().strip()
            if rol in ['tecnicos', 'admin']:
                btn_upd = QPushButton('ACTUALIZAR CALIBRACIÓN')
                btn_upd.setObjectName('ActionBtn')
                btn_upd.setFixedSize(220, 35)
                btn_upd.clicked.connect(lambda: self.modal_actualizar_patron(data, path_json))
                layout_acciones.addWidget(btn_upd)
                estado_actual = data.get('estado')
                txt_btn = 'MARCAR COMO APTO' if estado_actual == 'obsoleto' else 'MARCAR COMO OBSOLETO'
                btn_est = QPushButton(txt_btn)
                btn_est.setObjectName('ActionBtn')
                btn_est.setFixedSize(180, 35)
                btn_est.setStyleSheet('background-color: #e67e22; color: white; font-weight: bold; border-radius: 4px;')
                btn_est.clicked.connect(self.marcar_apto if estado_actual == 'obsoleto' else self.marcar_obsoleto)
                layout_acciones.addWidget(btn_est)
            if nombre_usuario == 'admin':
                btn_del = QPushButton('ELIMINAR')
                btn_del.setFixedSize(120, 35)
                btn_del.setStyleSheet('background-color: #c0392b; color: white; font-weight: bold; border-radius: 4px;')
                btn_del.clicked.connect(lambda ch, id_p=id_patron: self.borrar_elemento_fisico(id_p, 'patrones'))
                layout_acciones.addWidget(btn_del)
            layout_acciones.addStretch()
            self.layout_ficha_patron.addLayout(layout_acciones)
            self.layout_ficha_patron.addStretch()
            self.stack_patrones.setCurrentIndex(2)
            self.actualizar_arbol_contexto('elemento')
            
        except Exception as e:
            self.log(f'Error en ficha patrón: {e}', 'error')
            
    def subir_archivos(self):
        """Función para subir archivos desde la ficha técnica ya creada"""
        if not self.current_elemento_id:
            return
        
        file, _ = QFileDialog.getOpenFileName(self, 'Añadir documento')
        if file:
            tipo = getattr(self, 'current_tipo', 'instrumentos')
            destino = get_data_path(os.path.join('data', tipo, self.current_familia, self.current_elemento_id, 'documentos'))
            os.makedirs(destino, exist_ok=True)
            self.log(f'Archivo añadido a {self.current_elemento_id}')
            if tipo == 'patrones':
                self.cargar_ficha_patron(self.current_elemento_id)
    def actualizar_boton_estado(self, data):
        """Actualiza el texto y función del botón según el estado del elemento"""
        # ***<module>.MetrologiaApp.actualizar_boton_estado: Failure: Compilation Error
        if hasattr(self, 'btn_estado') and self.btn_estado:
            estado_actual = data.get('estado', 'normal')
            self.log(f'[DEBUG] Estado actual del elemento: {estado_actual}')
            if estado_actual == 'obsoleto':
                self.log('[DEBUG] Cambiando botón a MARCAR COMO APTO')
                self.btn_estado.setText('MARCAR COMO APTO')
                try:
                    self.btn_estado.clicked.disconnect()
                except:
                    pass
                self.btn_estado.clicked.connect(self.marcar_apto)
            else:
                self.log('[DEBUG] Cambiando botón a MARCAR COMO OBSOLETO')
                self.btn_estado.setText('MARCAR COMO OBSOLETO')
                try:
                    self.btn_estado.clicked.disconnect()
                except:
                    pass
                self.btn_estado.clicked.connect(self.marcar_obsoleto)
        else:
            self.log('[ERROR] No se encontró el botón btn_estado')
    def abrir_grafica_detallada(self, event, canvas):
        """Abre la ventana detallada de la gráfica al hacer click"""
        from gui.grafica_detail_window import GraficaDetailWindow
        id_elemento = getattr(self, 'current_elemento_id', None)
        familia = getattr(self, 'current_familia', None)
        historial = getattr(self, 'historial_actual', [])
        indice_seleccionado = (-1)
        if hasattr(self, 'tabla_calibraciones'):
            fila_visual = self.tabla_calibraciones.currentRow()
            if fila_visual >= 0:
                indice_seleccionado = len(historial) - 1 - fila_visual
        
        if id_elemento and familia:
                if not hasattr(self, '_grafica_detail_windows'):
                    self._grafica_detail_windows = {}
                if id_elemento in self._grafica_detail_windows:
                    try:
                        self._grafica_detail_windows[id_elemento].close()
                    except:
                        pass
                try:
                    ventana = GraficaDetailWindow(id_elemento, familia, historial, indice_seleccionado, self)
                    ventana.showMaximized()
                    self._grafica_detail_windows[id_elemento] = ventana
                except Exception as e:
                    self.log(f'[ERROR] No se pudo abrir la gráfica detallada: {e}')
        else:
                self.log('[ERROR] No hay id_elemento o familia para abrir gráfica')
        
        # Siempre limpiar el contenedor de gráficas antes de añadir una nueva
        for i in reversed(range(self.grafica_layout.count())):
            w = self.grafica_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        
        indice_real = len(self.historial_actual) - 1 - fila_visual
        if indice_real < 0 or indice_real >= len(self.historial_actual):
            return None
        
        from core.grafica_generator import crear_grafica_metrologia
        datos_para_grafica = {'historial': self.historial_actual, 'rango_min': getattr(self, '_current_rango_min', 0), 'rango_max': getattr(self, '_current_rango_max', 25)}
        self.canvas_grafica = crear_grafica_metrologia(datos_para_grafica, indice_seleccionado=indice_real)
        self.canvas_grafica.mousePressEvent = lambda event: self.abrir_grafica_detallada(event, self.canvas_grafica)
        self.grafica_layout.addWidget(self.canvas_grafica)
        
    def actualizar_tabla_puntos(self):
        """Actualiza la gráfica cuando se selecciona una calibración"""
        fila_visual = self.tabla_calibraciones.currentRow()
        if fila_visual < 0:
            return None
        
        # Siempre limpiar el contenedor de gráficas antes de añadir una nueva
        for i in reversed(range(self.grafica_layout.count())):
            w = self.grafica_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        
        indice_real = len(self.historial_actual) - 1 - fila_visual
        if indice_real < 0 or indice_real >= len(self.historial_actual):
            return None
        
        from core.grafica_generator import crear_grafica_metrologia
        datos_para_grafica = {'historial': self.historial_actual, 'rango_min': getattr(self, '_current_rango_min', 0), 'rango_max': getattr(self, '_current_rango_max', 25)}
        self.canvas_grafica = crear_grafica_metrologia(datos_para_grafica, indice_seleccionado=indice_real)
        self.canvas_grafica.mousePressEvent = lambda event: self.abrir_grafica_detallada(event, self.canvas_grafica)
        self.grafica_layout.addWidget(self.canvas_grafica)
        
    def create_bento_box(self, nombre, count, color='#0078d7'):
        # ***<module>.MetrologiaApp.create_bento_box: Failure: Compilation Error
        frame = QFrame()
        frame.setFixedSize(220, 140)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        color_map = {'Rojo': '#e74c3c', 'Azul': '#0078d7', 'Verde': '#2ecc71', 'Naranja': '#f39c12', 'Purpura': '#9b59b6', 'Rosa': '#ec407a', 'Cian': '#00bcd4'}
        border_color = color_map.get(color, color) if color.startswith('#') == False else color
        frame.setStyleSheet(f'''
            QFrame {{
                background-color: #2d2d30;
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: #3e3e42;
                border: 2px solid {border_color};
            }}
        ''')
        layout = QVBoxLayout(frame)
        title = QLabel(nombre.upper())
        title.setObjectName('BentoTitle')
        count_lbl = QLabel(f'Elementos: {count}')
        count_lbl.setObjectName('BentoCounter')
        frame.mousePressEvent = None  # Se establecerá después según el tipo
        layout.addWidget(title)
        layout.addWidget(count_lbl)
        layout.addStretch()
        return frame

    def explorar_familia(self, nombre_familia, tipo='instrumentos'):
        # ***<module>.MetrologiaApp.explorar_familia: Failure: Compilation Error
        self.current_familia = nombre_familia
        self.current_tipo = tipo
        if tipo == 'instrumentos':
            self.lbl_familia_titulo.setText(f'FAMILIA: {nombre_familia.upper()}')
            self.log(f'[MODO] Explorando familia: {nombre_familia}')
            self.stack.setCurrentIndex(1)
            self.refresh_tabla_elementos()
        else:
            self.lbl_patrones_titulo.setText(f'FAMILIA: {nombre_familia.upper()}')
            self.log(f'[MODO] Explorando familia: {nombre_familia}')
            self.stack_patrones.setCurrentIndex(1)
            self.refresh_lista_patrones()
        self.actualizar_arbol_contexto('familia')

    def calcular_proxima_calibracion(self, data):
        # irreducible cflow, using cdg fallback
        """Calcula la fecha de próxima calibración usando historial o raíz del JSON"""
        # ***<module>.MetrologiaApp.calcular_proxima_calibracion: Failure: Compilation Error
        pass
        periodicidad = int(data.get('periodicidad_meses', 12) or 12)
        historial = data.get('historial', [])
        ultima_calib_str = None
        if historial:
            ultima_calib_str = historial[(-1)].get('fecha_calibracion') or historial[(-1)].get('fecha_ultima_calibracion')
        if not ultima_calib_str:
            ultima_calib_str = data.get('FECHA_ULTIMA_CALIBRACION') or data.get('fecha_ultima_calibracion')
        try:
            fecha_ultima = datetime.strptime(str(ultima_calib_str).split()[0], '%Y-%m-%d') if ultima_calib_str and ultima_calib_str!= 'N/A' else None
            if fecha_ultima is None:
                return (None, None)
            proxima = fecha_ultima + relativedelta(months=periodicidad)
            return (proxima, str(ultima_calib_str))
        except Exception as e:
            self.log(f'[ERROR] Fallo en cálculo de fecha: {e}') if hasattr(self, 'log') else self
            return (None, None)

    def obtener_estado_calibracion(self, data):
        """Obtiene el estado del elemento de forma robusta"""
        # ***<module>.MetrologiaApp.obtener_estado_calibracion: Failure: Different bytecode
        if data.get('estado') == 'obsoleto':
            return 'OBSOLETO'
        else:
            from dateutil.relativedelta import relativedelta
            periodicidad = int(data.get('periodicidad_meses', 12) or 12)
            fecha_str = None
            if data.get('historial'):
                if len(data['historial']) > 0:
                    fecha_str = data['historial'][(-1)].get('fecha_calibracion')
            if not fecha_str:
                fecha_str = data.get('fecha_ultima_calibracion', '2000-01-01')
            try:
                if not fecha_str or fecha_str == 'N/A':
                    return 'SIN CALIBRAR'
                fecha_limpia = str(fecha_str).split(' ')[0]
                fecha_ultima = datetime.strptime(fecha_limpia, '%Y-%m-%d')
                fecha_caducidad = fecha_ultima + relativedelta(months=periodicidad)
                return 'APTO' if datetime.now() <= fecha_caducidad else 'NO APTO'
            except:
                return 'SIN CALIBRAR'
                
    def refresh_tabla_elementos(self):
        """Crea tarjetas de elementos con alertas de colores, estados dinámicos y avisos de fecha"""
        if not hasattr(self, 'layout_elementos') or self.layout_elementos is None:
            self.log('[ERROR] layout_elementos no existe')
            return
            
        while self.layout_elementos.count():
            item = self.layout_elementos.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        if not self.current_familia:
            return None
        else:
            ruta_familia = get_data_path(os.path.join('data', 'instrumentos', self.current_familia))
            if not os.path.exists(ruta_familia):
                return None
            else:
                elementos_info = []
                elementos = sorted([e for e in os.listdir(ruta_familia) if os.path.isdir(os.path.join(ruta_familia, e))])
                for elemento_id in elementos:
                    json_path = os.path.join(ruta_familia, elemento_id, f'{elemento_id}.json')
                    desc = 'Sin descripción'
                    estado = 'SIN CALIBRAR'
                    proxima_calib = None
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8', errors='ignore') as f:
                                data = json.load(f)
                                desc = data.get('descripcion', 'N/A')
                                estado = self.obtener_estado_calibracion(data)
                                proxima_calib, _ = self.calcular_proxima_calibracion(data)
                        except Exception as err:
                            self.log(f'[ERROR] Error leyendo JSON de {elemento_id}: {err}')
                    elementos_info.append({'id': elemento_id, 'descripcion': desc, 'estado': estado.upper(), 'proxima_calib': proxima_calib})
                orden_actual = self.combo_orden.currentText() if hasattr(self, 'combo_orden') else 'Nombre (A-Z)'
                if orden_actual == 'Próxima Calibración':
                    elementos_info.sort(key=lambda x: x['proxima_calib'] if x['proxima_calib'] else datetime(2099, 12, 31))
                else:
                    elementos_info.sort(key=lambda x: x['id'])
                hoy = datetime.now()
                umbral_15_dias = hoy + timedelta(days=15)
                for elem in elementos_info:
                    btn_wrapper = QPushButton()
                    btn_wrapper.setObjectName('WrapperBtn')
                    btn_wrapper.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_wrapper.setMinimumHeight(90)
                    card_layout = QHBoxLayout(btn_wrapper)
                    card_layout.setContentsMargins(15, 10, 15, 10)
                    info_layout = QVBoxLayout()
                    lbl_id = QLabel(f"{elem['id']} | {elem['descripcion']}")
                    lbl_id.setStyleSheet('font-weight: bold; font-size: 15px; color: #ffffff; border: none; background: none;')
                    fecha_str = elem['proxima_calib'].strftime('%Y-%m-%d') if elem['proxima_calib'] else 'N/A'
                    color_fecha = '#aaaaaa'
                    aviso_extra = ''
                    if elem['proxima_calib']:
                        if elem['proxima_calib'] < hoy:
                            color_fecha = '#ff4444'
                            aviso_extra = ' - [CADUCADO]'
                        elif elem['proxima_calib'] <= umbral_15_dias:
                            color_fecha = '#ffa500'
                            aviso_extra = ' - [URGENTE]'
                    lbl_fecha = QLabel(f'Próxima Calibración: {fecha_str}{aviso_extra}')
                    lbl_fecha.setStyleSheet(f'color: {color_fecha}; font-size: 12px; border: none; background: none;')
                    info_layout.addWidget(lbl_id)
                    info_layout.addWidget(lbl_fecha)
                    colores_estado = {'APTO': '#4ade80', 'NO APTO': '#ff4444', 'OBSOLETO': '#ff8c00', 'SIN CALIBRAR': '#9ca3af'}
                    color_est = colores_estado.get(elem['estado'], '#ffffff')
                    lbl_estado = QLabel(elem['estado'])
                    lbl_estado.setFixedWidth(120)
                    lbl_estado.setFixedHeight(30)
                    lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_estado.setStyleSheet(
                        f"""
                color: {color_est};
                border: 2px solid {color_est};
                border-radius: 15px;
                font-weight: bold;
                font-size: 11px;
                background-color: rgba(0, 0, 0, 20);
            """
                    )
                    card_layout.addLayout(info_layout)
                    card_layout.addStretch()
                    card_layout.addWidget(lbl_estado)
                    btn_wrapper.setStyleSheet(self.get_card_style('#27ae60'))
                    btn_wrapper.clicked.connect(lambda checked, id_el=elem['id']: self.cargar_ficha_elemento(id_el))
                    self.layout_elementos.addWidget(btn_wrapper)
                self.layout_elementos.addStretch()
                
        # Verificar el estado del scroll y container
        if hasattr(self, 'page_detalle'):
            self.page_detalle.update()
        if hasattr(self, 'scroll_elementos'):
            self.scroll_elementos.show()

    def refresh_lista_patrones(self):
        """Crea tarjetas de PATRONES con ordenación y misma estética que instrumentos"""
        # ***<module>.MetrologiaApp.refresh_lista_patrones: Failure: Different control flow
        while self.layout_lista_patrones.count():
            item = self.layout_lista_patrones.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if not hasattr(self, 'current_familia') or not self.current_familia:
            return None
        else:
            ruta_familia = get_data_path(os.path.join('data', 'patrones', self.current_familia))
            if not os.path.exists(ruta_familia):
                return None
            else:
                lista_elementos = []
                hoy = datetime.now()
                directorios = [e for e in os.listdir(ruta_familia) if os.path.isdir(os.path.join(ruta_familia, e))]
                for id_patron in directorios:
                    json_path = os.path.join(ruta_familia, id_patron, f'{id_patron}.json')
                    info = {'id': id_patron, 'descripcion': 'Patrón de medida', 'estado': 'SIN CALIBRAR', 'proxima': datetime(9999, 12, 31)}
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                info['descripcion'] = data.get('descripcion', 'N/A')
                                info['estado'] = self.obtener_estado_calibracion(data)
                                p, _ = self.calcular_proxima_calibracion(data)
                                if p:
                                    info['proxima'] = p
                        except:
                            pass
                    lista_elementos.append(info)
                criterio = self.combo_orden_pat.currentText()
                if criterio == 'Nombre (A-Z)':
                    lista_elementos.sort(key=lambda x: x['id'])
                else:
                    if criterio == 'Próxima Calibración':
                        lista_elementos.sort(key=lambda x: x['proxima'])
                for el in lista_elementos:
                    id_patron = el['id']
                    desc = el['descripcion']
                    estado = el['estado']
                    proxima = el['proxima']
                    btn_card = QPushButton()
                    btn_card.setObjectName('WrapperBtn')
                    btn_card.setMinimumHeight(90)
                    btn_card.setStyleSheet(self.get_card_style('#0078d7'))
                    card_layout = QHBoxLayout(btn_card)
                    info_layout = QVBoxLayout()
                    lbl_tit = QLabel(f'{id_patron} | {desc}')
                    lbl_tit.setStyleSheet('font-weight: bold; font-size: 15px; color: #ffffff; border: none; background: none;')
                    fecha_disp = proxima.strftime('%Y-%m-%d') if proxima.year!= 9999 else 'N/A'
                    color_f = '#aaaaaa'
                    if proxima < hoy:
                        color_f = '#ff4444'
                    lbl_f = QLabel(f'Próxima Calibración: {fecha_disp}')
                    lbl_f.setStyleSheet(f'color: {color_f}; font-size: 12px; border: none; background: none;')
                    info_layout.addWidget(lbl_tit)
                    info_layout.addWidget(lbl_f)
                    colores = {'APTO': '#4ade80', 'NO APTO': '#ff4444', 'OBSOLETO': '#ff8c00', 'SIN CALIBRAR': '#9ca3af'}
                    estado_str = estado.upper()
                    c_est = colores.get(estado_str, '#ffffff')
                    lbl_est = QLabel(estado_str)
                    lbl_est.setFixedWidth(120)
                    lbl_est.setFixedHeight(30)
                    lbl_est.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_est.setStyleSheet(f'color: {c_est}; border: 2px solid {c_est}; border-radius: 15px; font-weight: bold; background: rgba(0,0,0,40);')
                    card_layout.addLayout(info_layout)
                    card_layout.addStretch()
                    card_layout.addWidget(lbl_est)
                    btn_card.clicked.connect(lambda checked, id_el=id_patron: self.cargar_ficha_patron(id_el))
                    self.layout_lista_patrones.addWidget(btn_card)
                self.layout_lista_patrones.addStretch()

    def get_card_style(self, accent_color='#0078d4'):
        """Devuelve el CSS con fondo oscuro y resalte de borde en el color elegido"""
        return f'''
            QPushButton#WrapperBtn {{
                background-color: #252525 !important;
                border: 1px solid #3d3d3d !important;
                border-radius: 8px !important;
                margin-bottom: 6px !important;
                text-align: left !important;
                padding: 10px !important;
            }}
            QPushButton#WrapperBtn:hover {{
                background-color: #2d2d2d !important;
                border: 1px solid {accent_color} !important;
            }}
            QPushButton#WrapperBtn:pressed {{
                background-color: #1a1a1a !important;
            }}
        '''

    def setup_tree(self):
        """Genera el árbol lateral estilo VS Code limitado a la carpeta data"""
        dock = QDockWidget('Explorador', self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        
        # Ruta absoluta a la carpeta data
        path_data = get_data_path('data')
        if not os.path.exists(path_data):
            os.makedirs(path_data)
            
        self.model = QFileSystemModel()
        self.model.setRootPath(path_data) # El modelo vigila esta ruta
        self.model.setNameFilters([])
        self.model.setNameFilterDisables(True)

        class JsonFilterProxy(QSortFilterProxyModel):
            def filterAcceptsRow(self, source_row, source_parent):
                index = self.sourceModel().index(source_row, 0, source_parent)
                info = self.sourceModel().fileInfo(index)
                if info.isDir():
                    return True
                # Ocultar archivos .json y .hash
                return not (info.fileName().lower().endswith('.json') or info.fileName().lower().endswith('.hash'))

        self.proxy_model = JsonFilterProxy()
        self.proxy_model.setSourceModel(self.model)

        try:
            self.icon_provider = VSCIconProvider()
            self.model.setIconProvider(self.icon_provider)
        except Exception as e:
            self.log(f'No se pudieron cargar los iconos: {e}')

        self.tree = QTreeView()
        self.tree.setModel(self.proxy_model)
        
        # ESTO ES LO QUE TE FALTA: Limitar la vista a la carpeta data
        self.tree.setRootIndex(self.proxy_model.mapFromSource(self.model.index(path_data)))
        
        self.tree.setHeaderHidden(True)
        # Ocultar columnas de tamaño, tipo y fecha (solo dejar el nombre)
        for i in range(1, 4):
            self.tree.setColumnHidden(i, True)
            
        self.tree.doubleClicked.connect(self.on_tree_double_click)
        dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
    
    def actualizar_arbol_contexto(self, contexto):
        """Actualiza el árbol según donde estés navegando"""
        if not hasattr(self, 'tree') or not hasattr(self, 'model'):
            return

        # Forzar recarga del modelo sin perder iconos
        path_data = get_data_path('data')
        
        # Actualizar el path raíz para forzar recarga
        self.model.setRootPath("")
        self.model.setRootPath(path_data)
        
        # Asegurar que la raíz es correcta
        index_raiz = self.model.index(path_data)
        self.tree.setRootIndex(self.proxy_model.mapFromSource(index_raiz))
        
        if contexto == 'raiz':
            self.tree.collapseAll()
            # Obtener el tipo según la pestaña actual
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:  # INSTRUMENTOS
                ruta_instrumentos = get_data_path(os.path.join('data', 'instrumentos'))
                index_inst = self.model.index(ruta_instrumentos)
                if index_inst.isValid():
                    self.tree.expand(self.proxy_model.mapFromSource(index_inst))
            elif current_tab == 1:  # PATRONES
                ruta_patrones = get_data_path(os.path.join('data', 'patrones'))
                index_pat = self.model.index(ruta_patrones)
                if index_pat.isValid():
                    self.tree.expand(self.proxy_model.mapFromSource(index_pat))
            
        elif contexto == 'familia' and hasattr(self, 'current_familia') and self.current_familia:
            tipo = getattr(self, 'current_tipo', 'instrumentos')  # Usar el tipo actual, no el del tab
            path_familia = get_data_path(os.path.join('data', tipo, self.current_familia))
            index_fam = self.model.index(path_familia)
            if index_fam.isValid():
                index_fam_proxy = self.proxy_model.mapFromSource(index_fam)
                self.tree.expand(index_fam_proxy)
                self.tree.scrollTo(index_fam_proxy)
        elif contexto == 'elemento' and hasattr(self, 'current_familia') and self.current_familia:
            tipo = getattr(self, 'current_tipo', 'instrumentos')  # Usar el tipo actual, no el del tab
            path_familia = get_data_path(os.path.join('data', tipo, self.current_familia))
            index_fam = self.model.index(path_familia)
            if index_fam.isValid():
                index_fam_proxy = self.proxy_model.mapFromSource(index_fam)
                self.tree.expand(index_fam_proxy)
                self.tree.scrollTo(index_fam_proxy)
            if getattr(self, 'current_elemento_id', None):
                path_elemento = os.path.join(path_familia, self.current_elemento_id)
                index_ele = self.model.index(path_elemento)
                if index_ele.isValid():
                    index_ele_proxy = self.proxy_model.mapFromSource(index_ele)
                    self.tree.expand(index_ele_proxy)
                    self.tree.scrollTo(index_ele_proxy)


    def refresh_bento_view(self):
        """Refresca las vistas buscando la carpeta data de forma relativa al ejecutable"""
        # 1. Localizar la carpeta raíz del proyecto (donde esté main.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Construir rutas hacia la carpeta data
        ruta_ins = os.path.join(base_dir, 'data', 'instrumentos')
        ruta_pat = os.path.join(base_dir, 'data', 'patrones')

        # 3. Asegurar que las carpetas existan (para que no falle al distribuir)
        os.makedirs(ruta_ins, exist_ok=True)
        os.makedirs(ruta_pat, exist_ok=True)

        # 4. Cargar en los grids correspondientes - USAR LOS NOMBRES CORRECTOS
        if hasattr(self, 'bento_grid_inst'):
            self._llenar_grid_desde_disco(ruta_ins, self.bento_grid_inst)
            
        if hasattr(self, 'bento_grid_pat'):
            self._llenar_grid_desde_disco(ruta_pat, self.bento_grid_pat)
            
        self.log("[SISTEMA] Vistas sincronizadas con el repositorio de datos.")
    
    def _llenar_grid_desde_disco(self, arg1, arg2):
        """
        Reparación integral: El descompilador invirtió (grid, ruta_base).
        Esta función detecta el tipo de dato para no fallar.
        """
        # 1. Identificar quién es la ruta y quién es el layout
        if isinstance(arg1, str):
            ruta_base = arg1
            grid = arg2
        else:
            ruta_base = arg2
            grid = arg1

        # 2. Limpieza del grid (Layout) usando el método que no requiere argumentos
        if grid is not None and hasattr(grid, 'count'):
            while grid.count() > 0:
                item = grid.takeAt(0)
                if item is not None:
                    w = item.widget()
                    if w is not None:
                        w.deleteLater()

        # 3. Validación de la ruta
        if not ruta_base or not isinstance(ruta_base, str) or not os.path.exists(ruta_base):
            # Si no hay ruta o no existe, salimos sin error
            return

        # 4. Lógica de carga (Reconstruida según el estándar de tu app)
        try:
            self.log(f"[DEBUG] Cargando desde ruta: {ruta_base}")
            items_encontrados = [d for d in os.listdir(ruta_base) if os.path.isdir(os.path.join(ruta_base, d))]
            self.log(f"[DEBUG] Carpetas encontradas: {items_encontrados}")
            
            # Aquí el código suele usar un contador para las posiciones del Grid (filas, columnas)
            for i, nombre_item in enumerate(items_encontrados):
                fila = i // 4  # Ajusta según cuántas columnas quieras (ej: 4)
                columna = i % 4
                
                # Contar elementos dentro de la carpeta (los elementos son las subcarpetas directas)
                ruta_item = os.path.join(ruta_base, nombre_item)
                num_elementos = len([d for d in os.listdir(ruta_item) if os.path.isdir(os.path.join(ruta_item, d))]) if os.path.exists(ruta_item) else 0
                self.log(f"[DEBUG] Familia '{nombre_item}' tiene {num_elementos} elementos")
                
                # Determinar color según el tipo
                if 'patrones' in ruta_base:
                    color = '#0078d7'  # Azul para patrones
                else:
                    color = '#27ae60'  # Verde para instrumentos
                
                # Crear la tarjeta usando la función correcta
                widget_item = self.create_bento_box(nombre_item, num_elementos, color)
                widget_item.mousePressEvent = lambda e, n=nombre_item, t='patrones' if 'patrones' in ruta_base else 'instrumentos': self.explorar_familia(n, t)
                grid.addWidget(widget_item, fila, columna)
                self.log(f"[DEBUG] Tarjeta creada para '{nombre_item}'")
        except Exception as e:
            if hasattr(self, 'log'):
                self.log(f"Error cargando grid desde {ruta_base}: {e}")
            else:
                self.log(f"Error: {e}")
    
    def log(self, text):
        """Escribe en la consola si está disponible"""
        if hasattr(self, 'console') and self.console:
            self.console.append(text)

    def crear_familia(self, tipo='instrumentos'):
        """Crea una nueva carpeta de categoría en el disco"""
        titulo = 'Nueva Familia de Instrumentos' if tipo == 'instrumentos' else 'Nueva Familia de Patrones'
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setLabelText('Nombre de la categoría:')
        
        if dialog.exec():
            nombre = dialog.textValue().strip()
            if not nombre:
                return

            # OJO: Verifica si usas 'data' o 'db'
            path = get_data_path(os.path.join('data', tipo, nombre))
            
            try:
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True) # Creamos la carpeta
                    self.log(f'[INFO] Carpeta creada: {path}')
                    
                    # Intentamos refrescar la interfaz
                    try:
                        if hasattr(self, 'refresh_bento_view'):
                            self.refresh_bento_view()
                        self.log('[INFO] Vista principal actualizada')
                    except Exception as e:
                        self.log(f'[ERROR] Error refrescando vista: {str(e)}')
                else:
                    QMessageBox.warning(self, 'Error', 'La familia ya existe')
                    
            except Exception as e:
                self.log(f'[ERROR] No se pudo crear la carpeta: {str(e)}')
                QMessageBox.critical(self, 'Error', f'No se pudo crear la carpeta: {e}')
    
    def abrir_nuevo_elemento(self):
        """Abre formulario para crear nuevo elemento - Solo para técnicos"""
        
        # 1. Si no hay usuario, forzar Login
        if not self.current_user:
            d = LoginDialog(self)
            if d.exec():  # En PyQt6, exec() devuelve el resultado del diálogo
                self.current_user = d.get_username()
                self.user_type = d.get_user_type()
                if hasattr(self, 'logger') and self.logger:
                    self.logger.set_user(self.current_user)
                self.log(f'[LOGIN] {self.current_user} identificado como {self.user_type}.')
            else:
                return # Si cancela el login, salimos

        # 2. Verificar si es técnico
        if self.user_type != 'tecnicos':
            self.log(f'[SISTEMA] Acceso denegado: {self.current_user} no es técnico')
            QMessageBox.warning(self, 'Acceso Denegado', 'Solo los técnicos pueden crear nuevos elementos.')
            return

        # 3. Verificar si hay una familia seleccionada (el "or self.current_familia" estaba fatal)
        if not getattr(self, 'current_familia', None):
            QMessageBox.warning(self, 'Error de Contexto', 'Debes seleccionar una familia antes de añadir un elemento.')
            return

        # 4. Abrir la ventana de nuevo elemento
        try:
            tipo = getattr(self, 'current_tipo', 'instrumentos')
            self.ventana_nuevo = ElementWindow(self.current_familia, self.log, tipo_modulo=tipo)
            
            self.ventana_nuevo.tipo_modulo = tipo
            self.ventana_nuevo.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.ventana_nuevo.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            
            # Conexiones para refrescar las vistas al cerrar
            if hasattr(self, 'refresh_bento_view'):
                self.ventana_nuevo.destroyed.connect(self.refresh_bento_view)
            
            if tipo == 'instrumentos':
                if hasattr(self, 'refresh_tabla_elementos'):
                    self.ventana_nuevo.destroyed.connect(self.refresh_tabla_elementos)
            else:
                if hasattr(self, 'refresh_lista_patrones'):
                    self.ventana_nuevo.destroyed.connect(self.refresh_lista_patrones)
            
            self.ventana_nuevo.show()
            self.log(f'[SISTEMA] Abriendo formulario de {tipo}...')

        except Exception as e:
            self.log(f'[ERROR] No se pudo inicializar ElementWindow: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Fallo al abrir el formulario: {e}')
    
    def on_calibracion_click(self, row, column):
        """Maneja el clic en las fechas de calibración"""
        if row >= 0 and row < len(self.historial_actual):
                calibracion = self.historial_actual[row]
                self.log(f'[INFO] Calibración seleccionada: {calibracion.get('fecha_calibracion', 'N/A')}')
                self.actualizar_tabla_puntos()

    def on_tree_double_click(self, index):
        """Abre archivos con doble clic en el árbol"""
        # ***<module>.MetrologiaApp.on_tree_double_click: Failure: Different bytecode
        source_index = self.proxy_model.mapToSource(index)
        path = self.model.filePath(source_index)
        if path and os.path.exists(path):
            if os.path.isfile(path) and not path.lower().endswith('.json'):
                try:
                    if os.name == 'nt':
                        os.startfile(path)
                    else:
                        import subprocess
                        subprocess.run(['xdg-open', path])
                    self.log(f'[INFO] Archivo abierto: {path}')
                except Exception as e:
                    self.log(f'[ERROR] No se pudo abrir el archivo: {e}')
                    QMessageBox.warning(self, 'Error', f'No se pudo abrir el archivo:\n{e}')
    
    def setup_layout_bento_patrones(self):
        layout = QVBoxLayout(self.page_familias_patrones)
        self.scroll_pat = QScrollArea()
        self.scroll_pat.setWidgetResizable(True)
        self.scroll_pat.setStyleSheet('border: none; background-color: transparent;')
        self.bento_container_pat = QWidget()
        self.bento_grid_pat = QGridLayout(self.bento_container_pat)
        self.scroll_pat.setWidget(self.bento_container_pat)
        layout.addWidget(self.scroll_pat)
        
    def setup_page_instrumentos(self):
        """Configura la pestaña de instrumentos con stack para navegación"""
        layout = QVBoxLayout(self.page_instrumentos)
        self.stack = QStackedWidget()
        
        # Index 0: Bento de familias
        self.page_familias_inst = QWidget()
        layout_fam = QVBoxLayout(self.page_familias_inst)
        btn_add_fam = QPushButton('+ AGREGAR NUEVA FAMILIA')
        btn_add_fam.setObjectName('ActionBtn')
        btn_add_fam.clicked.connect(lambda checked, t='instrumentos': self.crear_familia(t))
        layout_fam.addWidget(btn_add_fam, alignment=Qt.AlignmentFlag.AlignLeft)
        self.scroll_inst = QScrollArea()
        self.scroll_inst.setWidgetResizable(True)
        self.scroll_inst.setStyleSheet('border: none; background-color: transparent;')
        self.bento_container_inst = QWidget()
        self.bento_grid_inst = QGridLayout(self.bento_container_inst)
        self.scroll_inst.setWidget(self.bento_container_inst)
        layout_fam.addWidget(self.scroll_inst)
        
        # Index 1: Detalle de elementos (ya creado en __init__)
        # self.page_detalle = QWidget()  # Ya existe - NO DUPLICAR
        # self.setup_page_detalle()  # Ya configurado en __init__ - NO DUPLICAR
        
        # Index 2: Ficha técnica
        self.page_ficha_tecnica = QWidget()
        self.setup_page_ficha_tecnica()
        
        # Agregar al stack
        self.stack.addWidget(self.page_familias_inst)
        self.stack.addWidget(self.page_detalle)
        self.stack.addWidget(self.page_ficha_tecnica)
        self.stack.setCurrentIndex(0)  # Empezar en el bento
        layout.addWidget(self.stack)

    def actualizar_tabla_proximos(self, button=None):
        """Lee los índices y rellena la tabla según el filtro"""
        filtro_actual = self.filter_group.checkedButton().property('filter_id')
        data_final = []
        hoy = datetime.now()
        try:
            archivos = []
            if filtro_actual in ['all', 'patrones']:
                archivos.append('index_patrones.json')
            if filtro_actual in ['all', 'instrumentos']:
                archivos.append('index_instrumentos.json')

            for arc in archivos:
                path = get_data_path(os.path.join('data', arc))
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data_final.extend(json.load(f))

            data_final.sort(key=lambda x: x.get('vencimiento', '9999-12-31'))
            self.tabla_proximos.setRowCount(len(data_final))

            for i, item in enumerate(data_final):
                venc_str = item.get('vencimiento', 'N/A')
                color_texto = '#d4d4d4'
                status_text = 'VIGENTE'
                
                if venc_str != 'N/A' and venc_str != '9999-12-31':
                    venc_dt = datetime.strptime(venc_str, '%Y-%m-%d')
                    dias_restantes = (venc_dt - hoy).days
                    if dias_restantes < 0:
                        color_texto = '#f44747'  # Rojo
                        status_text = 'CADUCADO'
                    elif dias_restantes <= 30:
                        color_texto = '#ce9178'  # Naranja/Marrón
                        status_text = 'URGENTE'

                row_data = [
                    item.get('id', ''), 
                    item.get('descripcion', ''), 
                    item.get('familia', ''), 
                    venc_str, 
                    status_text
                ]

                # Aquí es donde fallaba: hay que crear el QTableWidgetItem para cada celda
                for j, val in enumerate(row_data):
                    t_item = QTableWidgetItem(str(val)) # Creamos la variable que faltaba
                    t_item.setForeground(QColor(color_texto)) # Aplicamos el color de tu lógica
                    t_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.tabla_proximos.setItem(i, j, t_item)

        except Exception as e:
            # Uso self.log porque si el log falla, al menos lo ves en consola
            self.log(f'Error en tabla próximos: {e}')

    def limpiar_ficha_instrumento(self):
        """Limpia el contenido de la ficha de instrumento al volver"""
        # ***<module>.MetrologiaApp.limpiar_ficha_instrumento: Failure: Different control flow
        if hasattr(self, 'lbl_id_elemento'):
            self.lbl_id_elemento.setText('ID: ---')
        if hasattr(self, 'info_txt'):
            self.info_txt.clear()
        if hasattr(self, 'tabla_calibraciones'):
            self.tabla_calibraciones.setRowCount(0)
        if hasattr(self, 'tabla_puntos'):
            self.tabla_puntos.setRowCount(0)
        for i in hasattr(self, 'grafica_layout') and reversed(range(self.grafica_layout.count())):
                w = self.grafica_layout.itemAt(i).widget()
                w.setParent(None)
        self.current_elemento_id = None
        self.historial_actual = []
    def limpiar_ficha_patron(self):
        """Limpia el contenido de la ficha de patrón al volver"""
        # ***<module>.MetrologiaApp.limpiar_ficha_patron: Failure: Different control flow
        if hasattr(self, 'layout_ficha_patron') and self.layout_ficha_patron is not None and self.layout_ficha_patron.count():
                    item = self.layout_ficha_patron.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()
        self.current_elemento_id = None
    def borrar_elemento_fisico(self, id_elemento, tipo_folder):
        """
        Elimina físicamente la carpeta del elemento del disco.
        Solo permitido si el nombre de usuario es exactamente 'admin'.
        """
        # 1. Verificación de Seguridad
        if str(self.current_user).strip() != 'admin':
            self.log(f'[SEGURIDAD] Intento de borrado no autorizado por {self.current_user}')
            QMessageBox.critical(self, 'Acceso Denegado', "Solo la cuenta 'admin' puede realizar borrados físicos.")
            return

        # 2. Confirmación
        confirm = QMessageBox.question(
            self, 
            'Confirmar Eliminación', 
            f'¿Estás seguro de eliminar permanentemente {id_elemento}?\nEsta acción no se puede deshacer.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                # OJO: Verifica si tu carpeta es 'data' o 'db' (en antiguo.py usabas db)
                base_path = get_data_path(os.path.join('data', tipo_folder)) 
                ruta_a_borrar = ''
                
                if os.path.exists(base_path):
                    for familia in os.listdir(base_path):
                        posible_ruta = os.path.join(base_path, familia, id_elemento)
                        if os.path.exists(posible_ruta):
                            ruta_a_borrar = posible_ruta
                            break
                
                if ruta_a_borrar:
                    shutil.rmtree(ruta_a_borrar)
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.log_event('PHYSICAL_DELETE', f'{id_elemento} borrado por {self.current_user}')
                    
                    self.log(f'[ADMIN] {id_elemento} eliminado correctamente.')
                    
                    # Ejecutar re-indexación si la función existe
                    if generar_indices:
                        generar_indices()
                    
                    # Cambiar vista según el tipo
                    if tipo_folder == 'patrones':
                        self.stack_patrones.setCurrentIndex(1)
                    else:
                        # Corregido: antes decía self.stack_instrumentos, asegúrate que exista
                        if hasattr(self, 'stack_instrumentos'):
                            self.stack_instrumentos.setCurrentIndex(1)
                        else:
                            self.stack.setCurrentIndex(1) # Volver a gestión general
                else:
                    self.log(f'Error: No se encontró la ruta para {id_elemento}')
            
            except Exception as e:
                self.log(f'Error crítico al borrar: {str(e)}')

    def ir_a_ficha_desde_proximos(self, item):
        """Busca un elemento por ID en todas las carpetas y abre su ficha"""
        try:
            # 1. Obtener el ID del elemento desde la fila clicada
            fila = item.row()
            id_item = self.tabla_proximos.item(fila, 0)
            if not id_item:
                self.log("[ERROR] No se pudo obtener ID del elemento")
                return
            id_elemento = id_item.text()
            
            self.log(f"[DEBUG] Buscando elemento: {id_elemento}")
            
            tipo_encontrado = None
            familia_encontrada = None
            
            # 2. Buscar en qué carpeta (rama) y familia está el elemento
            for rama in ['instrumentos', 'patrones']:
                base_path = get_data_path(os.path.join('data', rama))
                self.log(f"[DEBUG] Buscando en: {base_path}")
                
                if not os.path.exists(base_path):
                    self.log(f"[DEBUG] No existe: {base_path}")
                    continue
                
                for fam in os.listdir(base_path):
                    ruta_fam = os.path.join(base_path, fam)
                    ruta_elemento = os.path.join(ruta_fam, id_elemento)
                    
                    if os.path.isdir(ruta_fam) and os.path.isdir(ruta_elemento):
                        tipo_encontrado = rama
                        familia_encontrada = fam
                        self.log(f"[DEBUG] ENCONTRADO: {rama}/{fam}/{id_elemento}")
                        break
                
                if tipo_encontrado:
                    break

            # 3. Navegación si se encuentra
            if not tipo_encontrado:
                self.log(f'[ERROR] No se encontró la ruta para el ID {id_elemento}')
                return
            
            self.log(f"[DEBUG] Tipo: {tipo_encontrado}, Familia: {familia_encontrada}")
            self.current_familia = familia_encontrada
            self.current_tipo = tipo_encontrado
            
            if tipo_encontrado == 'instrumentos':
                self.log("[DEBUG] Cambiando a pestaña INSTRUMENTOS (índice 0)")
                if hasattr(self, 'tab_widget'): 
                    self.tab_widget.setCurrentIndex(0)
                    self.log(f"[DEBUG] Tab actual: {self.tab_widget.currentIndex()}")
                
                self.log("[DEBUG] Cambiando stack a ficha técnica (índice 2)")
                self.stack.setCurrentIndex(2)
                self.log(f"[DEBUG] Stack actual: {self.stack.currentIndex()}")
                
                self.log(f"[DEBUG] Cargando ficha de elemento: {id_elemento}")
                self.cargar_ficha_elemento(id_elemento)
                
            else:  # patrones
                self.log("[DEBUG] Cambiando a pestaña PATRONES (índice 1)")
                if hasattr(self, 'tab_widget'): 
                    self.tab_widget.setCurrentIndex(1)
                    self.log(f"[DEBUG] Tab actual: {self.tab_widget.currentIndex()}")
                
                if hasattr(self, 'stack_patrones'):
                    self.log("[DEBUG] Cambiando stack_patrones a ficha (índice 2)")
                    self.stack_patrones.setCurrentIndex(2)
                else:
                    self.log("[DEBUG] Usando stack principal para patrones")
                    self.stack.setCurrentIndex(2)
                
                self.log(f"[DEBUG] Cargando ficha de patrón: {id_elemento}")
                self.cargar_ficha_patron(id_elemento)
                
            self.log(f'[INFO] Navegando a ficha de {id_elemento} ({tipo_encontrado})')

        except Exception as e:
            self.log(f'[ERROR] Error al saltar a ficha: {str(e)}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    # Resetear el flag de incremento de sesión para允许 incrementos en esta instancia
    from core.session_manager import reset_flag_incremento
    reset_flag_incremento()
    
    app = QApplication(sys.argv)
    window = MetrologiaApp()
    window.show()
    sys.exit(app.exec())