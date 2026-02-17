from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem,
                             QSplitter, QToolBar, QStatusBar, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import json
import numpy as np
import traceback



class GraficaDetailWindow(QMainWindow):
    def __init__(self, id_elemento, familia, historial_data, indice_seleccionado=-1, parent=None):
        super().__init__(parent)
        self.id_elemento = id_elemento
        self.familia = familia
        self.historial_data = historial_data
        self.indice_seleccionado = indice_seleccionado
        self.parent_main = parent
        
        self.setWindowTitle(f"Gráfica Detallada - {id_elemento}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Estilo oscuro consistente
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
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
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QTableWidget {
                background-color: #252526;
                border: 1px solid #3e3e42;
                gridline-color: #3e3e42;
                color: #d4d4d4;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3e3e42;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #cccccc;
                padding: 8px;
                border: 1px solid #3e3e42;
                font-weight: bold;
            }
        """)
        
        self.init_ui()
        self.cargar_datos_instrumento()
        self.crear_grafica()
        self.cargar_tabla_puntos()
        
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de herramientas
        self.create_toolbar()
        
        # Información del instrumento
        info_frame = QWidget()
        info_layout = QHBoxLayout(info_frame)
        
        self.lbl_info = QLabel(f"Instrumento: {self.id_elemento}")
        self.lbl_info.setStyleSheet("color: #0078d4; font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.lbl_info)
        
        info_layout.addStretch()
        
        self.lbl_stats = QLabel()
        info_layout.addWidget(self.lbl_stats)
        
        main_layout.addWidget(info_frame)
        
        # Splitter principal (gráfica izquierda, tabla derecha)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel de la gráfica
        self.grafica_widget = QWidget()
        self.grafica_layout = QVBoxLayout(self.grafica_widget)
        
        # Crear figura matplotlib
        self.figure = Figure(figsize=(10, 8), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #1e1e1e;")
        self.grafica_layout.addWidget(self.canvas)
        
        splitter.addWidget(self.grafica_widget)
        
        # Panel de la tabla
        self.tabla_widget = QWidget()
        self.tabla_layout = QVBoxLayout(self.tabla_widget)
        
        tabla_label = QLabel("Puntos de Calibración")
        tabla_label.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 10px;")
        self.tabla_layout.addWidget(tabla_label)
        
        self.tabla_puntos = QTableWidget()
        self.tabla_puntos.setColumnCount(6)
        self.tabla_puntos.setHorizontalHeaderLabels([
            "Fecha", "Valor Nominal", "Media", "Error", "Incertidumbre", "Estado"
        ])
        
        # Ajustar anchos de columnas
        header = self.tabla_puntos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Valor Nominal
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Media
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Error
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Incertidumbre
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Estado
        
        self.tabla_layout.addWidget(self.tabla_puntos)
        
        splitter.addWidget(self.tabla_widget)
        
        # Proporciones del splitter (70% gráfica, 30% tabla)
        splitter.setSizes([980, 420])
        
        main_layout.addWidget(splitter)
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
        
    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Acciones
        export_action = QAction("📊 Exportar PNG", self)
        export_action.triggered.connect(self.exportar_png)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction("🔄 Actualizar", self)
        refresh_action.triggered.connect(self.actualizar_datos)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        close_action = QAction("❌ Cerrar", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)
        
    def cargar_datos_instrumento(self):
        """Carga los datos del instrumento desde el JSON"""
        try:
            ruta_json = os.path.join("data/instrumentos", self.familia, self.id_elemento, f"{self.id_elemento}.json")
            with open(ruta_json, 'r', encoding='utf-8') as f:
                self.instrument_data = json.load(f)
                
            descripcion = self.instrument_data.get('descripcion', 'Sin descripción')
            rango_min = self.instrument_data.get('rango_min', 0)
            rango_max = self.instrument_data.get('rango_max', 0)
            
            self.lbl_info.setText(f"{self.id_elemento} - {descripcion} ({rango_min}-{rango_max}mm)")
            
        except Exception as e:
            # Mostramos un mensaje genérico al usuario; el detalle queda en el log JSON
            self.lbl_info.setText("Error cargando datos del instrumento.")
            from core.logger import get_logger
            logger = get_logger()
            logger.log_error('GRAFICA', str(e))
            logger.log_event('TRACEBACK', traceback.format_exc(), 'error')

    @staticmethod
    def _calcular_spline_manual(x, y, x_new):
        """Calcula la curva siguiendo las reglas: Lineal si < 3, Spline si >= 3 [cite: 2026-02-02]"""
        x, y = np.array(x), np.array(y)
        n = len(x)
        if n < 3:
            return np.interp(x_new, x, y) # Regla: Lineal [cite: 2026-02-02]
        
        # Regla: Spline Cúbico Natural manual [cite: 2026-02-02]
        h = np.diff(x)
        A = np.zeros((n, n))
        B = np.zeros(n)
        A[0, 0] = 1
        A[n-1, n-1] = 1
        for i in range(1, n-1):
            A[i, i-1] = h[i-1]
            A[i, i] = 2*(h[i-1] + h[i])
            A[i, i+1] = h[i]
            B[i] = 3*((y[i+1]-y[i])/h[i] - (y[i]-y[i-1])/h[i-1])
            
        c = np.linalg.solve(A, B)
        d = np.diff(c)/(3*h)
        b = np.diff(y)/h - h*(c[1:] + 2*c[:-1])/3
        
        y_new = np.zeros_like(x_new)
        for i, xi in enumerate(x_new):
            # Lógica mejorada: si xi está fuera del primer o último punto, 
            # usa el polinomio del tramo adyacente para extrapolar la curva suavemente
            if xi <= x[0]:
                idx = 0
                dx = xi - x[idx]
                y_new[i] = y[idx] + b[idx]*dx + c[idx]*dx**2 + d[idx]*dx**3
            elif xi >= x[-1]:
                idx = n - 2
                dx = xi - x[idx]
                y_new[i] = y[idx] + b[idx]*dx + c[idx]*dx**2 + d[idx]*dx**3
            else:
                idx = np.searchsorted(x, xi) - 1
                dx = xi - x[idx]
                y_new[i] = y[idx] + b[idx]*dx + c[idx]*dx**2 + d[idx]*dx**3
        return y_new
            
    def crear_grafica(self):
        """Crea la gráfica con el mismo sistema de velas que grafica_generator.py"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Configurar estilo oscuro
        ax.set_facecolor('#2a2a2a')
        self.figure.patch.set_facecolor('#1e1e1e')
        ax.grid(True, alpha=0.1, color='#d4d4d4')
        ax.spines['bottom'].set_color('#3e3e42')
        ax.spines['left'].set_color('#3e3e42')
        ax.spines['top'].set_color('#3e3e42')
        ax.spines['right'].set_color('#3e3e42')
        ax.tick_params(colors='#d4d4d4')
        ax.xaxis.label.set_color('#d4d4d4')
        ax.yaxis.label.set_color('#d4d4d4')
        
        if not self.historial_data:
            ax.text(0.5, 0.5, 'No hay datos de calibración', 
                   ha='center', va='center', transform=ax.transAxes, 
                   color='#888', fontsize=16)
            ax.set_xlabel('Valor Nominal (mm)', color='#d4d4d4')
            ax.set_ylabel('Error (mm)', color='#d4d4d4')
            ax.set_title('Gráfica de Calibración', color='#ccc', fontsize=16)
            self.canvas.draw()
            return
        
        # Usar la misma lógica que grafica_generator.py
        from core.grafica_generator import preparar_datos_velas
        
        # Preparar datos con velas para cada calibración
        colores_calibracion = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        # Configurar rango del eje X
        try:
            r_min = float(self.instrument_data.get('rango_min', 0))
            r_max = float(self.instrument_data.get('rango_max', 100))
            margen = (r_max - r_min) * 0.05 if r_max > r_min else 1
            ax.set_xlim(r_min - margen, r_max + margen)
        except:
            r_min, r_max = 0, 100
            ax.set_xlim(-5, 105)
        
        # Línea de referencia cero (Patrón)
        ax.axhline(y=0, color='#999999', linestyle='-', alpha=0.4, linewidth=1.5)
        
        # Dibujar solo la calibración seleccionada
        if self.indice_seleccionado >= 0 and self.indice_seleccionado < len(self.historial_data):
            calibracion = self.historial_data[self.indice_seleccionado]
        else:
            # Si no hay índice válido, usar la última calibración
            calibracion = self.historial_data[-1]
            self.indice_seleccionado = len(self.historial_data) - 1
        
        # Preparar datos para esta calibración específica
        temp_data = {'historial': [calibracion]}
        x, y_med, y_min, y_max = preparar_datos_velas(temp_data, 0)
        
        if x:
            fecha = calibracion.get('fecha_calibracion', '')[:10]
            apto = calibracion.get('apto', True)
            
            # Preparar datos de incertidumbre para cada punto
            incertidumbres = []
            for punto in calibracion.get('puntos', []):
                try:
                    valor_nom = float(punto.get('valor_nominal', 0))
                    # Buscar el valor nominal correspondiente en x
                    if valor_nom in x:
                        idx = x.index(valor_nom)
                        incert = float(punto.get('incertidumbre_k2', 0))
                        incertidumbres.append(incert)
                    else:
                        incertidumbres.append(0)
                except (ValueError, TypeError):
                    incertidumbres.append(0)
            
            # ORDENAR PUNTOS POR VALOR NOMINAL para evitar problemas con el spline
            if len(x) > 1:
                # Combinar datos y ordenar por valor nominal
                datos_ordenados = sorted(zip(x, y_med, y_min, y_max, incertidumbres))
                x, y_med, y_min, y_max, incertidumbres = zip(*datos_ordenados)
                x = list(x)
                y_med = list(y_med)
                y_min = list(y_min)
                y_max = list(y_max)
                incertidumbres = list(incertidumbres)
            
            # Velas de dispersión (min-max) - Rojas con más transparencia
            ax.vlines(x, y_min, y_max, color='#FF6B6B', linewidth=2, alpha=0.6)
            ax.scatter(x, y_min, color='#FF6B6B', marker='_', s=100, alpha=0.6)
            ax.scatter(x, y_max, color='#FF6B6B', marker='_', s=100, alpha=0.6)
            
            # Crear área de incertidumbre expandida
            if len(x) > 1 and any(inc > 0 for inc in incertidumbres):
                try:
                    # Usar spline manual en lugar de scipy
                    import numpy as np
                    
                    # Expandir a todo el rango del instrumento
                    r_min = float(self.instrument_data.get('rango_min', 0))
                    r_max = float(self.instrument_data.get('rango_max', 100))
                    x_expandido = np.linspace(r_min, r_max, 200)
                    
                    # Calcular valores expandidos usando spline manual
                    y_medio_expandido = self._calcular_spline_manual(x, y_med, x_expandido)
                    y_incert_expandido = self._calcular_spline_manual(x, incertidumbres, x_expandido)
                    
                    # Crear área de incertidumbre (superior e inferior)
                    y_superior = y_medio_expandido + y_incert_expandido
                    y_inferior = y_medio_expandido - y_incert_expandido
                    
                    # Dibujar área de incertidumbre con transparencia
                    ax.fill_between(x_expandido, y_inferior, y_superior, 
                                          color='#888888', alpha=0.2, 
                                          label='Área de Incertidumbre (k=2)')
                    
                    # Dibujar límites del área con líneas más finas
                    ax.plot(x_expandido, y_superior, color='#888888', linewidth=1, alpha=0.4)
                    ax.plot(x_expandido, y_inferior, color='#888888', linewidth=1, alpha=0.4)
                    
                except Exception as e:
                    # Si hay error, mostrar velas individuales
                    pass
            
            # Velas de incertidumbre (k=2) - Grises con más transparencia
            for i, (valor, incert) in enumerate(zip(x, incertidumbres)):
                if incert > 0:
                    # Vela de incertidumbre centrada en el error medio
                    y_center = y_med[i]
                    ax.vlines(valor, y_center - incert, y_center + incert, 
                             color='#888888', linewidth=2, alpha=0.4, 
                             label='Incertidumbre (k=2)' if i == 0 else "")
                    # Líneas horizontales en los extremos de la incertidumbre
                    ax.scatter([valor], [y_center - incert], color='#888888', marker='_', s=100, alpha=0.4)
                    ax.scatter([valor], [y_center + incert], color='#888888', marker='_', s=100, alpha=0.4)
            
            # Línea de tendencia (medias) - Azul
            ax.plot(x, y_med, marker='o', color='#3498db', linewidth=2, 
                   markersize=6, label=f'Error Medio ({fecha})')
            
            # Añadir información de estado en el título
            estado_texto = "APTO" if apto else "NO APTO"
            ax.set_title(f"Análisis de Comportamiento en Rango ({r_min}-{r_max} mm) - {fecha} - {estado_texto}", 
                        color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel("Punto de Medida en Escala (mm)", color='#d4d4d4', fontsize=12)
        ax.set_ylabel("Error (mm)", color='#d4d4d4', fontsize=12)
        
        # Leyenda
        legend = ax.legend(loc='best', framealpha=0.8, facecolor='#2a2a2a', edgecolor='#3e3e42')
        # Cambiar color del texto de la leyenda a gris claro
        for text in legend.get_texts():
            text.set_color('#d4d4d4')
        
        # Estadísticas de la calibración seleccionada
        if self.historial_data and self.indice_seleccionado >= 0:
            calibracion = self.historial_data[self.indice_seleccionado]
            puntos = calibracion.get('puntos', [])
            if puntos:
                errores = [abs(float(p.get('error', 0))) for p in puntos]
                max_error = max(errores) if errores else 0
                
                # Calcular incertidumbre máxima
                incerts = [float(p.get('incertidumbre_k2', 0)) for p in puntos]
                max_incert = max(incerts) if incerts else 0
                
                fecha = calibracion.get('fecha_calibracion', '')[:10]
                apto = calibracion.get('apto', True)
                estado = "APTO" if apto else "NO APTO"
                
                self.lbl_stats.setText(f"Error máx: {max_error:.4f}mm | Incert. máx: {max_incert:.4f}mm | {len(puntos)} puntos | {fecha} | {estado}")
        
        self.canvas.draw()
        
    def cargar_tabla_puntos(self):
        """Carga la tabla con solo los puntos de la calibración seleccionada"""
        self.tabla_puntos.setRowCount(0)
        
        # Obtener la calibración seleccionada
        if self.indice_seleccionado >= 0 and self.indice_seleccionado < len(self.historial_data):
            calibracion = self.historial_data[self.indice_seleccionado]
        else:
            # Si no hay índice válido, usar la última calibración
            calibracion = self.historial_data[-1] if self.historial_data else None
        
        if not calibracion:
            return
        
        puntos = calibracion.get('puntos', [])
        fecha_calibracion = calibracion.get('fecha_calibracion', '')[:10]
        
        # Configurar columnas para mostrar todas las lecturas
        # Primero, determinar el máximo número de lecturas para saber cuántas columnas necesitamos
        max_lecturas = 0
        for punto in puntos:
            lecturas = punto.get('lecturas', [])
            max_lecturas = max(max_lecturas, len(lecturas))
        
        # Configurar columnas: Fecha, Nominal, Incertidumbre, + columnas de lecturas
        num_columnas = 3 + max_lecturas
        self.tabla_puntos.setColumnCount(num_columnas)
        
        # Configurar headers
        headers = ['Fecha', 'Valor Nominal', 'Incertidumbre (k=2)']
        for i in range(max_lecturas):
            headers.append(f'Lectura {i+1}')
        
        self.tabla_puntos.setHorizontalHeaderLabels(headers)
        
        # Llenar la tabla
        for row, punto in enumerate(puntos):
            self.tabla_puntos.insertRow(row)
            
            # Fecha (misma para todos los puntos de esta calibración)
            self.tabla_puntos.setItem(row, 0, QTableWidgetItem(fecha_calibracion))
            
            # Valor Nominal
            valor_nom = float(punto.get('valor_nominal', 0))
            self.tabla_puntos.setItem(row, 1, QTableWidgetItem(f"{valor_nom:.4f}"))
            
            # Incertidumbre
            incert = float(punto.get('incertidumbre_k2', 0))
            incert_item = QTableWidgetItem(f"{incert:.4f}")
            self.tabla_puntos.setItem(row, 2, incert_item)
            
            # Todas las lecturas
            lecturas = punto.get('lecturas', [])
            for col, lectura in enumerate(lecturas):
                lectura_val = float(lectura)
                lectura_item = QTableWidgetItem(f"{lectura_val:.4f}")
                
                # Colorear según desviación del nominal
                desviacion = abs(lectura_val - valor_nom)
                if desviacion > incert * 1.5:  # Si la desviación es mayor que 1.5x la incertidumbre
                    lectura_item.setBackground(QColor('#e74c3c'))  # Rojo
                elif desviacion > incert:  # Si la desviación es mayor que la incertidumbre
                    lectura_item.setBackground(QColor('#f39c12'))  # Naranja
                
                self.tabla_puntos.setItem(row, 3 + col, lectura_item)
            
            # Rellenar celdas vacías si hay menos lecturas que el máximo
            for col in range(len(lecturas), max_lecturas):
                vacio_item = QTableWidgetItem("-")
                vacio_item.setBackground(QColor('#555555'))
                self.tabla_puntos.setItem(row, 3 + col, vacio_item)
        
        # Ajustar anchos de columnas
        header = self.tabla_puntos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Valor Nominal
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Incertidumbre
        
        # Las columnas de lecturas con tamaño fijo
        for i in range(3, num_columnas):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, 80)
        
        # Actualizar barra de estado
        self.status_bar.showMessage(f"Calibración del {fecha_calibracion}: {len(puntos)} puntos, {max_lecturas} lecturas máximas por punto")
        
    def exportar_png(self):
        """Exporta la gráfica como PNG"""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar gráfica", f"grafica_{self.id_elemento}.png", 
            "PNG Files (*.png)"
        )
        
        if filename:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight', 
                               facecolor='#1e1e1e', edgecolor='none')
            self.status_bar.showMessage(f"Gráfica guardada en {filename}")
            
    def actualizar_datos(self):
        """Actualiza los datos y regenera la gráfica"""
        self.cargar_datos_instrumento()
        self.crear_grafica()
        self.cargar_tabla_puntos()
        self.status_bar.showMessage("Datos actualizados")
        
    def closeEvent(self, event):
        """Se ejecuta al cerrar la ventana - limpia la referencia del padre"""
        if self.parent_main and hasattr(self.parent_main, '_grafica_detail_windows'):
            # Eliminar la referencia a esta ventana
            if self.id_elemento in self.parent_main._grafica_detail_windows:
                del self.parent_main._grafica_detail_windows[self.id_elemento]
        event.accept()
