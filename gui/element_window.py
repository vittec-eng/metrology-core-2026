from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QComboBox, QPushButton, QFileDialog, QLabel,
                             QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem, QDateEdit)
from PyQt6.QtCore import Qt, QDate
import json
import os
import shutil
import hashlib

class ElementWindow(QWidget):
    # Ahora aceptamos familia Y logger
    def __init__(self, familia, logger, tipo_modulo="instrumentos"): 
        super().__init__()
        self.familia = familia
        self.logger = logger
        self.tipo_modulo = tipo_modulo # <--- Lo guardamos aquí primero
        self.uploaded_files = []
        self.setWindowTitle(f"Nuevo {self.tipo_modulo[:-1]} en {self.familia}")
        self.setFixedSize(500, 600)
        self.init_ui()

    def init_ui(self):
        # Aplicar estilo oscuro consistente
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
                margin-bottom: 5px;
            }
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 8px;
                color: #d4d4d4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QComboBox {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 8px;
                color: #d4d4d4;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                border: 1px solid #3e3e42;
                color: #d4d4d4;
                selection-background-color: #0078d4;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #d4d4d4;
                font-size: 12px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #0078d4;
                border-radius: 4px;
                color: #0078d4;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #0078d4;
                color: white;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton#ActionBtn {
                background-color: #0078d4;
                color: white;
                border: 1px solid #0078d4;
            }
            QPushButton#ActionBtn:hover {
                background-color: #106ebe;
            }
        """)
        
        layout = QVBoxLayout()
        self.form = QFormLayout()

        self.codigo = QLineEdit()
        self.descripcion = QLineEdit()
        self.form.addRow("Código/ID:", self.codigo)
        self.form.addRow("Descripción:", self.descripcion)

        # CAMPOS DINÁMICOS SEGÚN TIPO
        if self.tipo_modulo == "patrones":
            self.valor_nominal = QLineEdit()
            self.incert_patron = QLineEdit()
            self.periodicidad = QSpinBox()
            self.periodicidad.setValue(12)
            self.fecha_ultima = QDateEdit()
            self.fecha_ultima.setDate(QDate.currentDate())
            self.fecha_ultima.setCalendarPopup(True)
            
            self.form.addRow("Valor Nominal (mm):", self.valor_nominal)
            self.form.addRow("Incertidumbre (k=2):", self.incert_patron)
            self.form.addRow("Periodicidad (Meses):", self.periodicidad)
            self.form.addRow("Fecha Última Calibración:", self.fecha_ultima)
        else:
            self.range_min = QLineEdit()
            self.range_max = QLineEdit()
            self.resolucion = QLineEdit()
            self.periodicidad = QSpinBox()
            self.periodicidad.setValue(12)
            self.fecha_compra = QDateEdit()
            self.fecha_compra.setDate(QDate.currentDate())
            self.fecha_compra.setCalendarPopup(True)
            self.fecha_ultima_calibracion = QDateEdit()
            self.fecha_ultima_calibracion.setDate(QDate.currentDate())
            self.fecha_ultima_calibracion.setCalendarPopup(True)
            self.tipo_patron = QComboBox()
            
            # Cargar dinámicamente las familias de patrones disponibles
            familias_patron = self.obtener_familias_patron()
            if familias_patron:
                self.tipo_patron.addItems(familias_patron)
            else:
                self.tipo_patron.addItems(["N/A"])
            
            self.form.addRow("Rango Mín:", self.range_min)
            self.form.addRow("Rango Máx:", self.range_max)
            self.form.addRow("Resolución:", self.resolucion)
            self.form.addRow("Periodicidad (Meses):", self.periodicidad)
            self.form.addRow("Fecha Compra:", self.fecha_compra)
            self.form.addRow("Fecha Última Calibración:", self.fecha_ultima_calibracion)
            self.form.addRow("Patrón Sugerido:", self.tipo_patron)

        layout.addLayout(self.form)

        # Sección de archivos
        layout.addWidget(QLabel("Documentos (PDF/JPG - Certificados, facturas, etc.):"))
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        layout.addWidget(self.files_list)
        
        # Botones de archivo
        btn_add_file = QPushButton("+ AGREGAR ARCHIVO")
        btn_add_file.setObjectName("ActionBtn")
        btn_add_file.clicked.connect(self.add_file)
        
        btn_remove_file = QPushButton("- REMOVER")
        btn_remove_file.clicked.connect(self.remove_file)
        
        files_layout = QHBoxLayout()
        files_layout.addWidget(btn_add_file)
        files_layout.addWidget(btn_remove_file)
        layout.addLayout(files_layout)
        
        # Botón de guardado
        btn_save = QPushButton("REGISTRAR")
        btn_save.setObjectName("ActionBtn") 
        btn_save.clicked.connect(self.save_element)
        
        layout.addWidget(btn_save)
        self.setLayout(layout)

    def add_file(self):
        """Permite seleccionar un archivo PDF o JPG"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar documentos",
            "",
            "Documentos (*.pdf *.jpg *.jpeg *.PNG *.JPG *.PDF);;Todos (*.*)"
        )
        
        for file in files:
            if file not in self.uploaded_files:
                self.uploaded_files.append(file)
                filename = os.path.basename(file)
                self.files_list.addItem(filename)
    
    def remove_file(self):
        """Elimina el archivo seleccionado de la lista"""
        current_row = self.files_list.currentRow()
        if current_row >= 0:
            self.uploaded_files.pop(current_row)
            self.files_list.takeItem(current_row)

    def obtener_familias_patron(self):
        """Busca familias de patrones en la carpeta data/patrones/"""
        ruta_patrones = os.path.join("data", "patrones")
        familias_encontradas = []
        
        if not os.path.exists(ruta_patrones):
            return familias_encontradas

        # Escanear directamente las carpetas dentro de data/patrones/
        for nombre_carpeta in os.listdir(ruta_patrones):
            ruta_completa = os.path.join(ruta_patrones, nombre_carpeta)
            if os.path.isdir(ruta_completa):
                familias_encontradas.append(nombre_carpeta)
                
        return familias_encontradas

    def verificar_codigo_global(self, codigo):
        """Verifica si el código existe en TODA la base de datos"""
        try:
            for root, dirs, files in os.walk("data"):
                for file in files:
                    if file.endswith(".json"):
                        ruta_json = os.path.join(root, file)
                        try:
                            with open(ruta_json, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, dict) and data.get("id") == codigo:
                                    return True
                        except (json.JSONDecodeError, KeyError, IOError):
                            # Ignorar archivos corruptos o sin formato válido
                            continue
        except Exception:
            pass
        return False

    def save_element(self):
        codigo = self.codigo.text().strip().upper()  # Homogeneizar a MAYÚSCULAS
        if not codigo: return

        # Verificar si ya existe el elemento EN TODA LA BASE DE DATOS
        if self.verificar_codigo_global(codigo):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Elemento Duplicado")
            msg_box.setText(f"El elemento '{codigo}' ya existe en otra familia.")
            msg_box.setInformativeText(f"Por favor, use un código diferente. El código '{codigo}' ya está siendo utilizado.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            return

        # Estructura base
        data = {
            "id": codigo,
            "familia": self.familia,
            "descripcion": self.descripcion.text(),
            "historial": []
        }

        if self.tipo_modulo == "patrones":
            # Formato BL-005
            val = self.valor_nominal.text().replace(',', '.')
            data.update({
                "valor_nominal": val,
                "periodicidad_meses": self.periodicidad.value(),
                "fecha_ultima_calibracion": self.fecha_ultima.date().toString("yyyy-MM-dd"),
                "patrones_sugeridos": "N/A",
                "incertidumbre": float(self.incert_patron.text().replace(',', '.') or 0)
            })
        else:
            # Formato ME-0002
            data.update({
                "rango_min": self.range_min.text().replace(',', '.'),
                "rango_max": self.range_max.text().replace(',', '.'),
                "resolucion": float(self.resolucion.text().replace(',', '.') or 0),
                "periodicidad_meses": self.periodicidad.value(),
                "fecha_compra": self.fecha_compra.date().toString("yyyy-MM-dd"),
                "fecha_ultima_calibracion": self.fecha_ultima_calibracion.date().toString("yyyy-MM-dd"),
                "patrones_sugeridos": self.tipo_patron.currentText(),
                "incertidumbre_elemento": 0.0
            })

        # Ruta de guardado: data/instrumentos o data/patrones
        ruta = os.path.join("data", self.tipo_modulo, self.familia, codigo)
        os.makedirs(ruta, exist_ok=True)
        
        ruta_json = os.path.join(ruta, f"{codigo}.json")
        
        # Importar la función unificada desde main
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import guardar_json_con_hash
        
        if guardar_json_con_hash(ruta_json, data, codigo):
            self.logger(f'[HASH] Hash generado para nuevo elemento {codigo}')
        else:
            self.logger(f'[ERROR] No se pudo generar hash para {codigo}')
            
        self.close()