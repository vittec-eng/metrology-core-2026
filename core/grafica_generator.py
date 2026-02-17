from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os

# Paleta técnica para la interfaz
COLORES = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B88B', '#52BE80']

def preparar_datos_velas(data, indice_seleccionado=-1):
    """
    Calcula min, max y media por cada punto nominal para el eje X real.
    Agrupa las lecturas para obtener la dispersion (velas).
    """
    if not data.get('historial'):
        return [], [], [], []
    
    # Usar el índice seleccionado o la última calibración por defecto
    if indice_seleccionado >= 0 and indice_seleccionado < len(data['historial']):
        calibracion = data['historial'][indice_seleccionado]
    else:
        calibracion = data['historial'][-1]
    
    puntos = calibracion.get('puntos', [])
    
    agrupados = {}
    for p in puntos:
        try:
            nom = float(p.get('valor_nominal', 0))
            lecturas = p.get('lecturas', [])
            # Errores individuales: Lectura - Nominal (base 0)
            errores = [float(l) - nom for l in lecturas]
            
            if nom not in agrupados:
                agrupados[nom] = []
            agrupados[nom].extend(errores)
        except (ValueError, TypeError):
            continue
    
    x_nominales = sorted(agrupados.keys())
    y_medias = [np.mean(agrupados[n]) for n in x_nominales]
    y_mins = [np.min(agrupados[n]) for n in x_nominales]
    y_maxs = [np.max(agrupados[n]) for n in x_nominales]
    
    return x_nominales, y_medias, y_mins, y_maxs

def crear_grafica_metrologia(data, indice_seleccionado=-1):
    """
    Funcion para la INTERFAZ (PyQt). 
    Muestra el sistema de velas sobre el RANGO TOTAL del equipo.
    """
    x, y_med, y_min, y_max = preparar_datos_velas(data, indice_seleccionado)
    
    fig = Figure(figsize=(8, 5), facecolor='#252526')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#1e1e1e')
    
    # Configuracion del Rango del Eje X
    r_min = float(data.get('rango_min', 0))
    r_max = float(data.get('rango_max', 100))
    margen = (r_max - r_min) * 0.05 if r_max > r_min else 1
    ax.set_xlim(r_min - margen, r_max + margen)
    
    if not x:
        ax.text(0.5, 0.5, 'Sin datos de calibracion', color='#d4d4d4', 
                ha='center', va='center', transform=ax.transAxes)
        return FigureCanvas(fig)

    # Linea de referencia cero (Patron)
    ax.axhline(y=0, color='#999999', linestyle='-', alpha=0.4, linewidth=1.5)
    
    # Dibujo de Velas (Dispersion Min-Max)
    ax.vlines(x, y_min, y_max, color='#FF6B6B', linewidth=2, alpha=0.8)
    ax.scatter(x, y_min, color='#FF6B6B', marker='_', s=100)
    ax.scatter(x, y_max, color='#FF6B6B', marker='_', s=100)
    
    # Linea de tendencia (Medias de error)
    ax.plot(x, y_med, marker='o', color='#3498db', linewidth=2, markersize=6)
    
    # Formato visual oscuro
    ax.set_title(f"Analisis de Comportamiento en Rango ({r_min}-{r_max} mm)", color='white', fontsize=10)
    ax.set_ylabel("Error (mm)", color='#d4d4d4')
    ax.tick_params(colors='#d4d4d4')
    ax.grid(True, alpha=0.1, color='#d4d4d4')
    
    for spine in ax.spines.values():
        spine.set_color('#3e3e42')
        
    fig.tight_layout()
    return FigureCanvas(fig)

def crear_grafica_pdf(data):
    import matplotlib
    matplotlib.use("Agg")  # backend NO interactivo
    import matplotlib.pyplot as plt
    """
    Funcion para el PDF. 
    Genera la grafica de velas con fondo blanco para impresion.
    """
    x, y_med, y_min, y_max = preparar_datos_velas(data)
    if not x: return None
    
    r_min = float(data.get('rango_min', 0))
    r_max = float(data.get('rango_max', 100))

    plt.ioff()

    plt.figure(figsize=(10, 5))
    plt.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    # Ajustar escala X al rango total del elemento
    margen = (r_max - r_min) * 0.05 if r_max > r_min else 1
    plt.xlim(r_min - margen, r_max + margen)
    
    # Velas de dispersion (Rojo)
    plt.vlines(x, y_min, y_max, color='red', linewidth=2, alpha=0.6, label='Dispersion (Min-Max)')
    plt.scatter(x, y_min, color='red', marker='_', s=100)
    plt.scatter(x, y_max, color='red', marker='_', s=100)
    
    # Linea de tendencia (Azul)
    plt.plot(x, y_med, marker='o', color='blue', linewidth=1.5, label='Error Medio')
    
    plt.title(f"Analisis de Precision en Rango Nominal: {r_min} a {r_max} mm")
    plt.xlabel("Punto de Medida en Escala (mm)")
    plt.ylabel("Error (mm)")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    
    # Guardado temporal para el PDF
    temp_path = f"data/temp_velas_{data.get('id')}.png"
    plt.savefig(temp_path, dpi=150, bbox_inches='tight')
    plt.close('all')
    return temp_path