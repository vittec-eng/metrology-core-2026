from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QLineEdit, QPushButton, QLabel, QSpinBox, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QLocale
from PyQt6 import QtCore
import os, json, datetime
import statistics
import hashlib
from core.pdf_generator import exportar_a_pdf

class CalibrationWindow(QWidget):
    def __init__(self, id_elemento, familia, logger, current_user=None):
        super().__init__()
        self.id_el = id_elemento
        self.familia = familia
        self.log = logger
        self.current_user = current_user
        self.setWindowTitle(f"Calibracion Dinamica: {id_elemento}")
        self.resize(1100, 750)
        self.puntos_widgets = [] 
        
        # Cargamos el rango una sola vez al inicio para validar
        self.cargar_limites_rango()
        self.init_ui()
        self.showMaximized()

    def cargar_limites_rango(self):
        """Carga los limites del equipo para validacion dinamica"""
        try:
            ruta_json = os.path.join("data/instrumentos", self.familia, self.id_el, f"{self.id_el}.json")
            with open(ruta_json, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                self.r_min = float(data.get('rango_min', 0))
                self.r_max = float(data.get('rango_max', 1000))
        except:
            self.r_min, self.r_max = 0, 1000

    def init_ui(self):
        # Aplicar estilo oscuro consistente con el resto de la aplicación
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: #cccccc;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 10px;
                color: #d4d4d4;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #0078d4;
                border-radius: 4px;
                color: #0078d4;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0078d4;
                color: white;
            }
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """)
        main_layout = QVBoxLayout(self)

        # --- BARRA SUPERIOR REFORZADA ---
        config_frame = QFrame()
        config_frame.setFixedHeight(90)
        config_frame.setStyleSheet("""
            QFrame { 
                background-color: #252526; 
                border-bottom: 2px solid #3e3e42; 
            }
            QLabel { font-weight: bold; color: #cccccc; }
        """)
        config_layout = QHBoxLayout(config_frame)

        # Información del instrumento a la izquierda
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        try:
            ruta_json = os.path.join("data/instrumentos", self.familia, self.id_el, f"{self.id_el}.json")
            with open(ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                descripcion = data.get('descripcion', 'Sin descripción')
                rango = f"{data.get('rango_min', 0)} - {data.get('rango_max', 0)} mm"
        except:
            descripcion = 'Sin descripción'
            rango = '0 - 1000 mm'
        
        # ID y Rango en la misma línea
        id_rango_frame = QFrame()
        id_rango_layout = QHBoxLayout(id_rango_frame)
        id_rango_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_id = QLabel(f"ID: {self.id_el}")
        lbl_id.setStyleSheet("color: #0078d4; font-size: 14px; font-weight: bold;")
        id_rango_layout.addWidget(lbl_id)
        
        id_rango_layout.addWidget(QLabel(" | "))
        
        lbl_rango = QLabel(f"Rango: {rango}")
        lbl_rango.setStyleSheet("color: #cccccc; font-size: 12px;")
        id_rango_layout.addWidget(lbl_rango)
        
        id_rango_layout.addStretch()
        info_layout.addWidget(id_rango_frame)
        
        # Descripción debajo
        lbl_desc = QLabel(f"{descripcion[:100]}{'...' if len(descripcion) > 100 else ''}")
        lbl_desc.setStyleSheet("color: #888888; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        info_layout.addWidget(lbl_desc)
        
        config_layout.addWidget(info_frame)
        config_layout.addStretch()

        # Controles de configuración a la derecha
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # Selector de Puntos
        controls_layout.addWidget(QLabel("Puntos de medición:"))
        self.spin_puntos = QSpinBox()
        self.spin_puntos.setRange(1, 25)
        self.spin_puntos.setValue(5)
        self.spin_puntos.setFixedSize(100, 30)
        self.spin_puntos.setStyleSheet("""
            QSpinBox {
                font-size: 14px; 
                padding: 5px;
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QSpinBox::up-button {
                width: 20px;
            }
            QSpinBox::down-button {
                width: 20px;
            }
        """)
        controls_layout.addWidget(self.spin_puntos)

        # Selector de Lecturas
        controls_layout.addWidget(QLabel("Lecturas por punto:"))
        self.spin_mediciones = QSpinBox()
        self.spin_mediciones.setRange(1, 15)
        self.spin_mediciones.setValue(5)
        self.spin_mediciones.setFixedSize(100, 30)
        self.spin_mediciones.setStyleSheet("""
            QSpinBox {
                font-size: 14px; 
                padding: 5px;
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QSpinBox::up-button {
                width: 20px;
            }
            QSpinBox::down-button {
                width: 20px;
            }
        """)
        controls_layout.addWidget(self.spin_mediciones)

        # Botón Generar
        btn_generar = QPushButton("GENERAR INTERFAZ")
        btn_generar.setFixedSize(200, 35)
        btn_generar.setObjectName("ActionBtn")
        btn_generar.setStyleSheet("""
            QPushButton { 
                background-color: #0078d4; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                border-radius: 6px; 
            }
            QPushButton:hover { background-color: #106ebe; }
        """)
        btn_generar.clicked.connect(self.dibujar_puntos)
        controls_layout.addWidget(btn_generar)
        
        config_layout.addWidget(controls_frame)
        main_layout.addWidget(config_frame)

        # --- ÁREA DE SCROLL ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #1e1e1e; }")
        
        self.container = QWidget()
        self.flow_layout = QHBoxLayout(self.container) 
        self.flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        # --- BOTÓN GUARDAR (TAMAÑO NORMAL) ---
        footer_layout = QHBoxLayout()
        self.btn_save = QPushButton("GUARDAR CALIBRACIÓN")
        self.btn_save.setFixedSize(250, 40) # Tamaño mas controlado
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #2ea043; color: white; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #3fb950; }
        """)
        self.btn_save.clicked.connect(self.save_calibration)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_save)
        footer_layout.addStretch()
        main_layout.addLayout(footer_layout)

    def validar_valor(self, texto, widget):
        """Valida si el punto nominal esta en el rango del equipo"""
        try:
            val = float(texto.replace(',', '.') or 0)
            if val < self.r_min or val > self.r_max:
                # Rojo si esta fuera de rango
                widget.setStyleSheet("background-color: #3c3c3c; color: white; border: 2px solid #FF6B6B; border-radius: 3px; padding: 4px;")
            else:
                # Normal si es correcto
                widget.setStyleSheet("background-color: #3c3c3c; color: white; border: 1px solid #555; border-radius: 3px; padding: 4px;")
        except:
            pass

    def calcular_proxima_calibracion(self, data):
        
        from dateutil.relativedelta import relativedelta
        try:
            periodicidad = int(data.get('periodicidad_meses', 12))
            historial = data.get('historial', [])
            ultima_calib_str = None

            if historial and len(historial) > 0:
                # Ojo: usamos el split para limpiar posibles horas
                ultima_calib_str = historial[-1].get('fecha_calibracion')
            
            if not ultima_calib_str:
                ultima_calib_str = data.get('fecha_ultima_calibracion') or data.get('FECHA_ULTIMA_CALIBRACION')

            if ultima_calib_str and ultima_calib_str != 'N/A':
                try:
                    fecha_limpia = str(ultima_calib_str).split(' ')[0]
                    fecha_ultima = datetime.strptime(fecha_limpia, '%Y-%m-%d')
                    proxima = fecha_ultima + relativedelta(months=periodicidad)
                    return proxima, str(ultima_calib_str)
                except:
                    return None, None
            
            return None, None
        except:
            return None, None




    def cargar_patrones_disponibles(self):
        """Carga patrones filtrados por rango, incertidumbre > 0 y fecha en vigor"""
        try:
            patrones = []
            base_patrones = os.path.join("data", "patrones")
            fecha_hoy = datetime.datetime.datetime.now() # Para comparar vigencia
            
            if os.path.exists(base_patrones):
                for familia in os.listdir(base_patrones):
                    familia_path = os.path.join(base_patrones, familia)
                    if os.path.isdir(familia_path):
                        for patron_id in os.listdir(familia_path):
                            json_path = os.path.join(familia_path, patron_id, f"{patron_id}.json")
                            
                            if os.path.exists(json_path):
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    
                                    # 1. Validar Incertidumbre (Debe existir y ser > 0)
                                    incert = float(data.get('incertidumbre', 0))
                                    if incert <= 0:
                                        continue # Salta este patrón si no tiene incertidumbre válida

                                    # 2. Validar Vigencia (Usa tu función de cálculo)
                                    proxima_dt, _ = self.calcular_proxima_calibracion(data)
                                    if not proxima_dt or proxima_dt < fecha_hoy:
                                        # Opcional: Loguear qué patrón está caducado
                                        # self.log(f"[SISTEMA] Patrón {patron_id} ignorado por caducidad.")
                                        continue

                                    # 3. Validar Rango Nominal
                                    valor_nominal = float(data.get('valor_nominal', 0))
                                    if self.r_min <= valor_nominal <= self.r_max:
                                        patrones.append({
                                            'id': patron_id,
                                            'valor_nominal': valor_nominal,
                                            'incertidumbre': incert,
                                            'descripcion': data.get('descripcion', ''),
                                            'proxima_calib': proxima_dt.strftime('%Y-%m-%d') # Útil para la nota del PDF
                                        })
            
            patrones.sort(key=lambda x: x['valor_nominal'])
            return patrones
            
        except Exception as e:
            self.log(f"[ERROR] Cargando patrones: {e}")
            return []

    def calcular_puntos_sugeridos(self, num_puntos):
        """Selecciona patrones de forma ascendente y repartida"""
        puntos_sugeridos = []
        
        # 1. Aseguramos que los patrones estén ordenados de menor a mayor nominal
        patrones_ordenados = sorted(self.patrones_disponibles, key=lambda x: x['valor_nominal'])
        total_disponibles = len(patrones_ordenados)

        if total_disponibles == 0:
            return []

        # 2. Si pedimos más puntos de los que hay, los damos todos en orden
        if num_puntos >= total_disponibles:
            return patrones_ordenados

        # 3. Si hay suficientes, seleccionamos N patrones repartidos proporcionalmente
        # Esto asegura que si tienes 20 patrones y pides 5 puntos, elija 
        # el primero, el último y 3 intermedios de forma equilibrada.
        for i in range(num_puntos):
            # Calculamos el índice proporcional
            idx = int(i * (total_disponibles - 1) / (num_puntos - 1)) if num_puntos > 1 else 0
            puntos_sugeridos.append(patrones_ordenados[idx])
            
        return puntos_sugeridos

    def dibujar_puntos(self):
        # 1. Cargar patrones y resolución del equipo
        self.patrones_disponibles = self.cargar_patrones_disponibles()
        
        try:
            ruta_json = os.path.join("data/instrumentos", self.familia, self.id_el, f"{self.id_el}.json")
            with open(ruta_json, 'r', encoding='utf-8') as f:
                data_res = json.load(f)
            
            # Forzamos formato string para contar decimales correctamente (evita el error de los 2 decimales)
            res_val_raw = data_res.get('resolucion', 0.001)
            res_str = "{:.10f}".format(float(res_val_raw)).rstrip('0')
            if '.' in res_str:
                decimales_max = len(res_str.split('.')[-1])
            else:
                decimales_max = 2
            
            incert_historica = float(data_res.get('incertidumbre_elemento', 0.005))
        except:
            decimales_max = 3
            incert_historica = 0.005

        # 2. Limpiar interfaz anterior
        while self.flow_layout.count():
            child = self.flow_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        self.puntos_widgets = []
        num_puntos = self.spin_puntos.value()
        num_mediciones = self.spin_mediciones.value()
        puntos_sugeridos = self.calcular_puntos_sugeridos(num_puntos)

        # 3. Generar los cuadros de cada punto
        for i in range(num_puntos):
            punto_frame = QFrame()
            punto_frame.setFixedWidth(280)
            punto_frame.setStyleSheet("""
                QFrame { background-color: #252526; border: 1px solid #3e3e42; border-radius: 8px; }
                QLabel { color: #85c1e2; font-size: 12px; font-weight: bold; padding-top: 5px; }
            """)
            
            p_layout = QVBoxLayout(punto_frame)
            lbl_title = QLabel(f"PUNTO {i+1}")
            lbl_title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
            p_layout.addWidget(lbl_title)

            p_layout.addWidget(QLabel("ID PATRÓN"))
            combo_patron = QComboBox()
            combo_patron.setStyleSheet("""
                QComboBox {
                    background-color: #2a2a2a;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #888;
                    margin-right: 5px;
                }
            """)
            for patron in self.patrones_disponibles:
                display_text = f"{patron['id']} ({patron['valor_nominal']}mm)"
                combo_patron.addItem(display_text, patron)
            
            if i < len(puntos_sugeridos):
                for j in range(combo_patron.count()):
                    if combo_patron.itemData(j)['id'] == puntos_sugeridos[i]['id']:
                        combo_patron.setCurrentIndex(j)
                        break
            p_layout.addWidget(combo_patron)

            p_layout.addWidget(QLabel("VALOR NOMINAL"))
            edit_val_patron = QLineEdit()
            edit_val_patron.setReadOnly(True)
            edit_val_patron.setStyleSheet("background-color: #2a2a2a;")
            p_layout.addWidget(edit_val_patron)

            p_layout.addWidget(QLabel("INCERT. PATRÓN"))
            edit_incert = QLineEdit()
            edit_incert.setReadOnly(True)
            edit_incert.setStyleSheet("background-color: #2a2a2a;")
            p_layout.addWidget(edit_incert)

            def update_fields(idx, evp=edit_val_patron, ei=edit_incert, cb=combo_patron):
                if idx >= 0:
                    data_p = cb.itemData(idx)
                    evp.setText(str(data_p['valor_nominal']))
                    ei.setText(str(data_p['incertidumbre']))
            
            combo_patron.currentIndexChanged.connect(update_fields)
            update_fields(combo_patron.currentIndex())

            p_layout.addWidget(QLabel(f"LECTURAS (MÁX {decimales_max} DEC.)"))
            from PyQt6.QtGui import QDoubleValidator
            validador = QDoubleValidator(0.0, 1000.0, decimales_max)
            validador.setNotation(QDoubleValidator.Notation.StandardNotation)
            # Aquí usamos el locale para asegurar que acepte el punto correctamente
            validador.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

            lecturas_inputs = []
            for j in range(num_mediciones):
                inp = QLineEdit()
                inp.setValidator(validador) 
                inp.setPlaceholderText(f"0.{'0'*decimales_max}")
                inp.setStyleSheet("""
                    QLineEdit {
                        background-color: #2a2a2a;
                        border: 1px solid #555;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 13px;
                        min-height: 16px;
                    }
                    QLineEdit:focus {
                        border: 2px solid #0078d4;
                    }
                """)
                
                def validar_consistencia(widget=inp, nom_w=edit_val_patron, inc_h=incert_historica):
                    try:
                        texto = widget.text().replace(',', '.')
                        if texto:
                            val = float(texto)
                            nom = float(nom_w.text().replace(',', '.'))
                            if inc_h > 0:
                                self.mostrar_aviso_metrologico(val, nom, inc_h)
                    except ValueError:
                        pass

                inp.editingFinished.connect(validar_consistencia)
                p_layout.addWidget(inp)
                lecturas_inputs.append(inp)

            self.flow_layout.addWidget(punto_frame)
            self.puntos_widgets.append({
                "combo_patron": combo_patron,
                "val_patron": edit_val_patron,
                "inc_patron": edit_incert,
                "lecturas": lecturas_inputs
            })

    def save_calibration(self):
        try:
            datos_puntos = []
            errores = []

            # --- PASO 1: Cargar el JSON primero para obtener la resolución ---
            ruta_json = os.path.join("data/instrumentos", self.familia, self.id_el, f"{self.id_el}.json")
            with open(ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer resolución del JSON y calcular su componente (u_res)
            res_val = float(data.get('resolucion', 0.001))
            u_res = res_val / (12**0.5)
            
            for p in self.puntos_widgets:
                # Obtener datos del combobox
                combo_patron = p["combo_patron"]
                if combo_patron.currentIndex() < 0:
                    continue  # Saltar si no hay patrón seleccionado
                
                patron_seleccionado = combo_patron.itemData(combo_patron.currentIndex())
                val_nom_raw = p["val_patron"].text().replace(',', '.')
                if not val_nom_raw: continue
                
                val_nom = float(val_nom_raw)
                
                # Validación de seguridad final antes de guardar
                if val_nom < self.r_min or val_nom > self.r_max:
                    self.log(f"[ERROR] Bloqueado: Punto {val_nom} fuera de rango ({self.r_min}-{self.r_max})")
                    return

                id_patron = patron_seleccionado['id']
                u_patron = float(p["inc_patron"].text().replace(',', '.') or 0)
                u_patron_tipica = u_patron / 2
                lecturas = [float(l.text().replace(',', '.') or 0) for l in p["lecturas"]]               
                media = statistics.mean(lecturas)
                error = media - val_nom
                errores.append(error)
                
                n = len(lecturas)
                std_dev = statistics.stdev(lecturas) if n > 1 else 0
                uA = std_dev / (n**0.5)
                
                # CÁLCULO COHERENTE: Incluimos u_res en la suma cuadrática
                uc = (uA**2 + u_patron_tipica**2 + u_res**2)**0.5
                U_expandida = uc * 2  # Incertidumbre expandida (k=2)
                U_expandida = max(U_expandida, res_val) # Aseguramos que no sea menor que la resolución
                
                datos_puntos.append({
                    "id_patron": id_patron,
                    "valor_nominal": round(val_nom, 4),
                    "media_lecturas": round(media, 4),
                    "error": round(error, 4),
                    "incertidumbre_k2": round(U_expandida, 4),
                    "lecturas": [round(l, 4) for l in lecturas]
                })

            # --- CORRECCIÓN DEL ERROR 'STR' OBJECT HAS NO ATTRIBUTE 'GET' ---
            if isinstance(self.current_user, dict):
                responsable = self.current_user.get('username', 'Admin')
            else:
                responsable = str(self.current_user) if self.current_user else 'Admin'

            # Volvemos a abrir para actualizar historial
            with open(ruta_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            nueva_entrada = {
                "fecha_calibracion": datetime.datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "responsable": responsable,
                "puntos": datos_puntos,
                "error_maximo": round(max([abs(e) for e in errores]), 4),
                "apto": max([abs(e) for e in errores]) < 0.05
            }
            data['historial'].append(nueva_entrada)
            data['fecha_ultima_calibracion'] = nueva_entrada['fecha_calibracion']
            data['incertidumbre'] = nueva_entrada['incertidumbre_k2']

            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # --- GENERAR NUEVO HASH ---
            try:
                SAL_SECRETA = b"METROLOGIA_2024_HASH_SALT_SECURE"  # Palabra secreta para mayor seguridad
                hash_sha256 = hashlib.sha256()
                with open(ruta_json, "rb") as f:
                    contenido = f.read()
                    hash_sha256.update(contenido + SAL_SECRETA)
                hash_valor = hash_sha256.hexdigest()
                
                ruta_hash = ruta_json.replace('.json', '.hash')
                with open(ruta_hash, 'w', encoding='utf-8') as f:
                    f.write(hash_valor)
                    
                self.log(f"[HASH] Hash actualizado para {self.id_el} tras calibración")
            except Exception as e:
                self.log(f"[ERROR] No se pudo actualizar hash para {self.id_el}: {e}")

            # --- EXPORTACIÓN PDF ---
            self.log("[DEBUG] Iniciando exportación PDF...")
            exportar_a_pdf(data, ruta_json) 
            self.log(f"[EXITO] Calibración guardada y PDF generado.")
            
            # --- REGISTRO DE IMPRESIÓN EN LOG ---
            elemento_id = data.get('id', 'N/A')
            fecha_calibracion = nueva_entrada.get('fecha_calibracion', 'N/A')
            
            # Generar ID del informe para el log
            if fecha_calibracion != 'N/A':
                try:
                    fecha_iso = fecha_calibracion.split()[0]  # YYYY-MM-DD
                    id_informe = f"ICI-{elemento_id}-{fecha_iso.replace('-', '')}"
                except:
                    id_informe = f"ICI-{elemento_id}-{datetime.datetime.now().strftime('%Y%m%d')}"
                    fecha_iso = datetime.datetime.now().strftime('%Y-%m-%d')
            else:
                id_informe = f"ICI-{elemento_id}-{datetime.datetime.now().strftime('%Y%m%d')}"
                fecha_iso = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Usar el logger del sistema para guardar en metrologia_log.json
            from core.logger import get_logger
            logger = get_logger()
            logger.log_event("DATA", f"ICI generado: {id_informe} para {elemento_id}. Fecha calibración: {fecha_iso}")
            
            if self.parent():
                self.parent().cargar_ficha_elemento(self.id_el)
            
            self.close()

        except Exception as e:
            self.log(f"[ERROR] Datos invalidos: {e}")


    def mostrar_aviso_metrologico(self, lectura, nominal, incert_ref):
        """Muestra un aviso si la lectura se desvía más de 3 veces la incertidumbre"""
        from PyQt6.QtWidgets import QMessageBox
        error_detectado = abs(lectura - nominal)
        # Usamos un factor de k=3 (confianza extrema) para no ser pesados con el aviso
        limite_aviso = incert_ref * 3 
        
        if error_detectado > limite_aviso:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Aviso de Consistencia")
            msg.setText(f"La lectura {lectura}mm parece inusual.")
            msg.setInformativeText(
                f"El error detectado ({error_detectado:.4f}) es muy superior a la "
                f"incertidumbre histórica del equipo ({incert_ref:.4f}).\n\n"
                "¿Es correcta la medición?"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
