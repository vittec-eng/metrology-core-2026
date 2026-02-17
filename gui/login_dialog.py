import json
import sys
import os
from base64 import b64encode, b64decode
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_data_path(relative_path):
    """Obtiene la ruta a los datos de la aplicación"""
    if hasattr(sys, '_MEIPASS'):
        # Modo empaquetado: los datos están en _internal
        return os.path.join(os.path.dirname(sys.executable), '_internal', relative_path)
    else:
        # Modo desarrollo
        return os.path.join(os.path.abspath("."), relative_path)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        # Configuración de encriptación
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
        self.setWindowTitle("Acceso Técnico - Metrology Core 2026")
        
        # Aumentamos el tamaño para que respire mejor el diseño
        self.setFixedSize(350, 220) 
        # --- CÓDIGO PARA CENTRAR ---
        # Obtenemos la geometría de la ventana principal (o de la pantalla)
        geo = self.frameGeometry()
        # Buscamos el punto central de la pantalla donde está el cursor o la app
        centro = self.screen().availableGeometry().center()
        # Movemos el centro de nuestra geometría al centro de la pantalla
        geo.moveCenter(centro)
        # Movemos la ventana a la posición calculada
        self.move(geo.topLeft())
        # ---------------------------

        self.user_data = None 

        # Aplicamos estilos CSS (QSS) para igualar tu captura
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
                margin-bottom: 10px;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 14px;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #0078d4;
                border-radius: 4px;
                color: #0078d4;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 10px;
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
        layout.setContentsMargins(30, 20, 30, 20) # Más aire en los bordes
        
        self.header = QLabel("Identificación requerida para edición:")
        self.username = QLineEdit(placeholderText="Usuario")
        self.password = QLineEdit(placeholderText="Contraseña")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        
        btn_login = QPushButton("Entrar")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor) # Cursor de mano al pasar
        btn_login.clicked.connect(self.validate)
        
        layout.addWidget(self.header)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(btn_login)
        self.setLayout(layout)

    def encriptar_password(self, password):
        """Encripta una contraseña usando Fernet (AES)"""
        if not password or password.startswith("encrypted:"):
            return password
        encrypted_password = self.cipher_suite.encrypt(password.encode())
        return "encrypted:" + b64encode(encrypted_password).decode()

    def desencriptar_password(self, password):
        """Desencripta una contraseña usando Fernet (AES)"""
        if not password or not password.startswith("encrypted:"):
            return password
        encrypted_password = password[10:]
        encrypted_password = b64decode(encrypted_password)
        decrypted_password = self.cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode()

    def validate(self):
        try:
            with open(get_data_path('config/users.json'), 'r') as f:
                data = json.load(f)
                
                password_ingresada = self.password.text()
                
                for u in data['tecnicos']:
                    if u['username'] == self.username.text():
                        # Comparar con la contraseña almacenada (puede estar encriptada o no)
                        password_almacenada = u['password']
                        if password_almacenada.startswith('encrypted:'):
                            # Desencriptar la contraseña almacenada y comparar
                            password_desencriptada = self.desencriptar_password(password_almacenada)
                            if password_ingresada == password_desencriptada:
                                u['user_type'] = 'tecnicos'
                                self.user_data = u
                                self.accept()
                                return
                        else:
                            # Comparar contraseñas en texto plano (compatibilidad hacia atrás)
                            if password_ingresada == password_almacenada:
                                u['user_type'] = 'tecnicos'
                                self.user_data = u
                                self.accept()
                                return
                
                for u in data['visor']:
                    if u['username'] == self.username.text():
                        # Comparar con la contraseña almacenada (puede estar encriptada o no)
                        password_almacenada = u['password']
                        if password_almacenada.startswith('encrypted:'):
                            # Desencriptar la contraseña almacenada y comparar
                            password_desencriptada = self.desencriptar_password(password_almacenada)
                            if password_ingresada == password_desencriptada:
                                u['user_type'] = 'visor'
                                self.user_data = u
                                self.accept()
                                return
                        else:
                            # Comparar contraseñas en texto plano (compatibilidad hacia atrás)
                            if password_ingresada == password_almacenada:
                                u['user_type'] = 'visor'
                                self.user_data = u
                                self.accept()
                                return
                
                QMessageBox.warning(self, "Error", "Credenciales incorrectas")
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"No se pudo leer users.json: {e}")
    
    def get_user_data(self):
        """Devuelve el diccionario completo del usuario autenticado"""
        return self.user_data
    
    def get_username(self):
        if self.user_data:
            return self.user_data.get('username', 'Unknown')
        return None
    
    def get_user_type(self):
        if self.user_data:
            return self.user_data.get('user_type', 'visor')
        return None