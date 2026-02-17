import json
import hashlib
from base64 import b64encode, b64decode
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class GestionUsuariosDialog(QDialog):

    def __init__(self, parent=None):
        # Clave de encriptación derivada de una contraseña maestra
        self.CLAVE_MAESTRA = "METROLOGIA_2024_SECURE_KEY_MASTER"
        self.salt = b"metrologia_salt_2024"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = b64encode(kdf.derive(self.CLAVE_MAESTRA.encode()))
        self.cipher_suite = Fernet(key)
        super().__init__(parent)
        self.init_ui()

    def encriptar_password(self, password):
        """Encripta una contraseña usando Fernet (AES)"""
        if not password or password.startswith("encrypted:"):
            return password
        encrypted_password = self.cipher_suite.encrypt(password.encode())
        return "encrypted:" + b64encode(encrypted_password).decode()

    def desencriptar_password(self, encrypted_password):
        """Desencripta una contraseña"""
        if not encrypted_password or not encrypted_password.startswith("encrypted:"):
            return encrypted_password
        try:
            encrypted_data = b64decode(encrypted_password[10:])  # Quita "encrypted:"
            decrypted_password = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_password.decode()
        except Exception:
            return encrypted_password  # Si falla, devuelve el original

    def init_ui(self):
        try:
            self.setWindowTitle("Gestión de usuarios")
            self.resize(700, 450)
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #333333;
                    border-radius: 8px;
                }
                QLabel {
                    color: #cccccc;
                    font-size: 13px;
                    margin-bottom: 5px;
                }
                QTableWidget {
                    background-color: #252526;
                    border: 1px solid #3e3e42;
                    border-radius: 4px;
                    gridline-color: #3e3e42;
                    selection-background-color: #0078d4;
                }
                QTableWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #3e3e42;
                }
                QTableWidget::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #2d2d30;
                    color: #cccccc;
                    padding: 8px;
                    border: 1px solid #3e3e42;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #1a1a1a;
                    border: 1px solid #0078d4;
                    border-radius: 4px;
                    color: #0078d4;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #0078d4;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            
            layout = QVBoxLayout()
            
            # Tabla
            self.tabla = QTableWidget(0, 4)
            self.tabla.setHorizontalHeaderLabels(["Usuario", "Contraseña", "Nombre", "Rol"])
            layout.addWidget(self.tabla)
            
            # Layout de botones
            btn_layout = QHBoxLayout()
            
            btn_add = QPushButton("+ Añadir Usuario")
            btn_delete = QPushButton("Eliminar Seleccionado")
            btn_save = QPushButton("GUARDAR EN JSON")
            btn_save.setStyleSheet("background-color: #2c3e50; font-weight: bold; color: white;")
            
            # CONECTAR LOS BOTONES AQUÍ - ANTES DE AÑADIRLOS AL LAYOUT
            btn_save.clicked.connect(lambda: self.guardar_datos())
            btn_add.clicked.connect(lambda: self.añadir_fila())
            btn_delete.clicked.connect(lambda: self.eliminar_fila())
            
            btn_layout.addWidget(btn_add)
            btn_layout.addWidget(btn_delete)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_save)
            
            layout.addLayout(btn_layout)
            self.setLayout(layout)
            
            # Añadir la carga de datos
            self.ruta_json = 'config/users.json'
            self.cargar_datos()

            
        except Exception as e:
            self.log(f"[ERROR]: {e}")
            import traceback
            traceback.print_exc()

    def cargar_datos(self):
        try:         
            if not os.path.exists(self.ruta_json):
                return
                
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Limpiar tabla
                self.tabla.setRowCount(0)
               
                # Cargar técnicos
                tecnicos = data.get('tecnicos', [])
                for i, u in enumerate(tecnicos):
                    row = self.tabla.rowCount()
                    self.tabla.insertRow(row)
                    self.tabla.setItem(row, 0, QTableWidgetItem(str(u.get('username', ''))))
                    # Desencriptar contraseña para mostrarla
                    password = self.desencriptar_password(str(u.get('password', '')))
                    self.tabla.setItem(row, 1, QTableWidgetItem(password))
                    self.tabla.setItem(row, 2, QTableWidgetItem(str(u.get('nombre_completo', ''))))
                    self.tabla.setItem(row, 3, QTableWidgetItem("tecnico"))
                    
                # Cargar visores
                visores = data.get('visor', [])
                for i, u in enumerate(visores):
                    row = self.tabla.rowCount()
                    self.tabla.insertRow(row)
                    self.tabla.setItem(row, 0, QTableWidgetItem(str(u.get('username', ''))))
                    # Desencriptar contraseña para mostrarla
                    password = self.desencriptar_password(str(u.get('password', '')))
                    self.tabla.setItem(row, 1, QTableWidgetItem(password))
                    self.tabla.setItem(row, 2, QTableWidgetItem(str(u.get('nombre_completo', ''))))
                    self.tabla.setItem(row, 3, QTableWidgetItem("visor"))

                    
        except Exception as e:
            import traceback
            traceback.print_exc()

    def añadir_fila(self):
        try:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 3, QTableWidgetItem("visor"))

        except Exception as e:
            self.log(f"[ERROR en añadir_fila]: {e}")

    def eliminar_fila(self):
        try:
            current_row = self.tabla.currentRow()
            if current_row >= 0:
                user_item = self.tabla.item(current_row, 0)
                if user_item and user_item.text() == "admin":
                    QMessageBox.warning(self, "Protección", "No se puede borrar el admin.")
                    return
                self.tabla.removeRow(current_row)
        except Exception as e:
            self.log(f"[ERROR en eliminar_fila]: {e}")

    def guardar_datos(self):
        try:
            nuevo_json = {"tecnicos": [], "visor": []}
            
            for i in range(self.tabla.rowCount()):
                user = {
                    "username": self.tabla.item(i, 0).text() if self.tabla.item(i, 0) else "",
                    # Encriptar contraseña antes de guardar
                    "password": self.encriptar_password(self.tabla.item(i, 1).text() if self.tabla.item(i, 1) else ""),
                    "nombre_completo": self.tabla.item(i, 2).text() if self.tabla.item(i, 2) else ""
                }
                rol = self.tabla.item(i, 3).text().lower() if self.tabla.item(i, 3) else "visor"
                
                if "tecnico" in rol:
                    nuevo_json["tecnicos"].append(user)
                else:
                    nuevo_json["visor"].append(user)
            
            with open(self.ruta_json, 'w', encoding='utf-8') as f:
                json.dump(nuevo_json, f, indent=4)
            
            QMessageBox.information(self, "Éxito", "Cambios guardados.\n\nLas contraseñas han sido encriptadas.")
            self.accept()
            
        except Exception as e:
            self.log(f"[ERROR en guardar_datos]: {e}")
            QMessageBox.critical(self, "Error", f"Fallo al guardar: {e}")
