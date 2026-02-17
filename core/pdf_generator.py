from fpdf import FPDF
from datetime import datetime
from .grafica_generator import crear_grafica_pdf
import os
import unicodedata

def limpiar_texto_pdf(texto):
    """
    Convierte caracteres españoles a sus equivalentes sin acentos para compatibilidad con FPDF
    """
    if not texto:
        return "N/A"
    
    # Reemplazos de vocales con acentos (conservando la letra base)
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                    if unicodedata.category(c) != 'Mn')
    
    return texto

class PDFGenerador(FPDF):
    def __init__(self, numero_informe="S/N"):
        super().__init__()
        self.numero_informe = numero_informe

    def header(self):
        """Encabezado profesional con ID de Informe"""
        # Fondo del encabezado (Azul oscuro Metrology Core)
        self.set_fill_color(41, 56, 71) 
        self.rect(0, 0, 210, 35, 'F')
        
        # Título Principal (Sin acentos para evitar errores de fuentes estándar)
        self.set_font("Arial", "B", 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "INFORME DE CALIBRACION INTERNA", 0, 1, "C")
        
        # ID DEL INFORME
        self.set_font("Arial", "B", 12)
        self.set_text_color(200, 200, 200)
        self.cell(0, 7, f"ID INFORME: {self.numero_informe}", 0, 1, "C")
        
        # Subtítulo App
        self.set_font("Arial", "I", 8)
        self.set_text_color(170, 170, 170)
        self.cell(0, 5, "METROLOGY CORE 2026 - SISTEMA DE GESTION DE ACTIVOS", 0, 1, "C")
        
        self.ln(10)

    def footer(self):
            """Pie de página técnico con conteo total"""
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(100, 100, 100)
            self.set_draw_color(200, 200, 200)
            self.line(10, 282, 200, 282)
            
            # Usamos {nb} que FPDF reemplazará por el total de páginas al final
            texto_pagina = f"Pagina {self.page_no()} de {{nb}} | Generado por Metrology Core"
            
            self.cell(0, 10, limpiar_texto_pdf(texto_pagina), 0, 0, "L")
            self.cell(0, 10, f"Fecha impresion: {datetime.now().strftime('%d/%m/%Y')}", 0, 0, "R")
        
def exportar_a_pdf(data, ruta_entrada):
    """
    Genera el PDF del informe ICI con todos los digitos a 4 decimales
    y grafica de tendencia lineal.
    """
    # 1. Determinacion de la ruta de salida
    id_elemento = data.get('id', 'N/A')
    fecha_cal = datetime.now().strftime('%Y%m%d')
    
    if data.get('historial'):
        ultima = data['historial'][-1]
        ultima_fecha = ultima.get('fecha_calibracion', '')
        if ultima_fecha:
            # Extrae YYYYMMDD de "YYYY-MM-DD HH:MM"
            fecha_cal = ultima_fecha.split()[0].replace("-", "")

    id_informe = f"ICI-{id_elemento}-{fecha_cal}"
    
    # Si la ruta_entrada es un directorio, creamos el nombre del archivo
    if os.path.isdir(ruta_entrada):
        ruta_final = os.path.join(ruta_entrada, f"{id_informe}.pdf")
    else:
        # Si es una ruta completa a un archivo, la respetamos o usamos su directorio
        directorio = os.path.dirname(ruta_entrada)
        ruta_final = os.path.join(directorio, f"{id_informe}.pdf")

    # 2. Creacion del documento
    pdf = PDFGenerador(numero_informe=id_informe)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Añadir fuente que soporte UTF-8
    try:
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 10)
    except:
        # Si no hay DejaVu, usar Arial con limpieza
        pdf.set_font("Arial", "", 10)
    
    # --- BLOQUE 1: IDENTIFICACION DEL ELEMENTO ---
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(41, 56, 71)
    pdf.cell(0, 8, f"FICHA TECNICA DEL EQUIPO: {id_elemento}", 0, 1)
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    # Limpieza completa de caracteres para FPDF
    desc = limpiar_texto_pdf(data.get('descripcion', 'N/A'))
    patrones = limpiar_texto_pdf(data.get('patrones_sugeridos', 'N/A'))
    responsable = limpiar_texto_pdf(ultima.get('responsable', 'N/A'))
    
    col_w = 45
    pdf.cell(col_w, 6, "Descripcion:", 0, 0); pdf.set_font("Arial", "B", 10); pdf.cell(0, 6, desc, 0, 1); pdf.set_font("Arial", "", 10)
    pdf.cell(col_w, 6, "Rango de medida:", 0, 0); pdf.cell(0, 6, f"{data.get('rango_min', 'N/A')} - {data.get('rango_max', 'N/A')} mm", 0, 1)
    pdf.cell(col_w, 6, "Periodicidad:", 0, 0); pdf.cell(0, 6, f"{data.get('periodicidad_meses', 'N/A')} meses", 0, 1)
    pdf.cell(col_w, 6, "Patrones utilizados:", 0, 0); pdf.cell(0, 6, patrones, 0, 1)
    pdf.ln(3)

    # --- BLOQUE 2: RESULTADOS DE LA CALIBRACION ---
    if data.get('historial'):
        ultima = data['historial'][-1]
        
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "  RESUMEN DE CALIBRACION", 0, 1, fill=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", "", 10)
        # Formatear fecha de calibración a formato europeo DD/MM/YYYY
        fecha_cal_formateada = ultima.get('fecha_calibracion', 'N/A')
        if fecha_cal_formateada != 'N/A':
            try:
                # Convertir de "YYYY-MM-DD HH:MM:SS" a "DD/MM/YYYY"
                fecha_dt = datetime.strptime(fecha_cal_formateada.split()[0], '%Y-%m-%d')
                fecha_cal_formateada = fecha_dt.strftime('%d/%m/%Y')
            except:
                pass  # Si hay error, dejar formato original
        
        pdf.cell(60, 6, f"Fecha: {fecha_cal_formateada}", 0, 0)
        pdf.cell(60, 6, f"Responsable: {responsable}", 0, 1)
        pdf.ln(3)

        # TABLA DE MEDICIONES (Cabecera)
        pdf.set_font("Arial", "B", 8)
        pdf.set_fill_color(41, 56, 71)
        pdf.set_text_color(255, 255, 255)
        
        pdf.cell(10, 8, "Pto", 1, 0, "C", True)
        pdf.cell(22, 8, "ID Patron *", 1, 0, "C", True)
        pdf.cell(22, 8, "Nominal", 1, 0, "C", True)
        pdf.cell(22, 8, "Media", 1, 0, "C", True)
        pdf.cell(22, 8, "Error (E)", 1, 0, "C", True)
        pdf.cell(22, 8, "Incert. (U)", 1, 0, "C", True)
        pdf.cell(40, 8, "Incert. Total (|E|+U)", 1, 0, "C", True)
        pdf.cell(28, 8, "Resultado", 1, 1, "C", True)

        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(0, 0, 0)
        
        for idx, punto in enumerate(ultima.get('puntos', []), 1):
            # Formateo estricto a 4 decimales
            try:
                nominal = float(punto.get('valor_nominal', 0))
                media = float(punto.get('media_lecturas', 0))
                error = float(punto.get('error', 0))
                incert = float(punto.get('incertidumbre_k2', 0))
                total = abs(error) + incert
            except (ValueError, TypeError):
                nominal = media = error = incert = total = 0.0
            
            pdf.cell(10, 7, str(idx), 1, 0, "C")
            pdf.cell(22, 7, limpiar_texto_pdf(str(punto.get('id_patron', 'N/A'))), 1, 0, "C")
            pdf.cell(22, 7, f"{nominal:.4f}", 1, 0, "C")
            pdf.cell(22, 7, f"{media:.4f}", 1, 0, "C")
            pdf.cell(22, 7, f"{error:.4f}", 1, 0, "C")
            pdf.cell(22, 7, f"{incert:.4f}", 1, 0, "C")
            
            pdf.set_font("Arial", "B", 8)
            pdf.cell(40, 7, f"{total:.4f} mm", 1, 0, "C")
            pdf.set_font("Arial", "", 8)
            
            # Color segun estado APTO/NO APTO
            pdf.set_text_color(39, 174, 96) if ultima.get('apto') else pdf.set_text_color(231, 76, 60)
            pdf.cell(28, 7, "APTO" if ultima.get('apto') else "FUERA TOL.", 1, 1, "C")
            pdf.set_text_color(0, 0, 0)

        # --- NOTA DE CONFORMIDAD DE TRAZABILIDAD ---
        pdf.ln(1)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(100, 100, 100)
        
        # Formatear fecha de calibración a formato europeo DD/MM/YYYY
        fecha_nota = ultima.get('fecha_calibracion', datetime.now().strftime('%Y-%m-%d')).split()[0]
        try:
                # Convertir de "YYYY-MM-DD" a "DD/MM/YYYY"
                fecha_dt = datetime.strptime(fecha_nota, '%Y-%m-%d')
                fecha_nota = fecha_dt.strftime('%d/%m/%Y')
        except:
                pass  # Si hay error, dejar formato original
        
        texto_conformidad = f"* Metrology Core 2026 ha comprobado que, segun los datos proporcionados " \
                           f"por el usuario a la base de datos de la aplicacion, todos los patrones " \
                           f"utilizados son validos a fecha {fecha_nota}."
        
        # Limpiamos el texto para evitar errores de caracteres y lo pintamos
        pdf.multi_cell(0, 4, limpiar_texto_pdf(texto_conformidad), 0, "L")
        pdf.set_text_color(0, 0, 0) # Reset al color negro

        # --- BLOQUE 3: ANALISIS GRAFICO ---
        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 8, "  ANALISIS GRAFICO DE DESVIACION LINEAL", 0, 1, fill=True)
        
        # Llamada al generador de grafica (ahora usa eje X en mm)
        grafica_path = crear_grafica_pdf(data)
        if grafica_path and os.path.exists(grafica_path):
            # Centrar la imagen en el ancho A4 (210mm)
            pdf.image(grafica_path, x=20, y=pdf.get_y() + 5, w=160)
            pdf.set_y(pdf.get_y() + 95)
            try:
                os.remove(grafica_path)
            except:
                pass

    # Nota tecnica final
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "Nota tecnica:", 0, 1)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, "La Incertidumbre Total reportada (|E|+U) representa el error maximo probable. "
                         "El usuario debe aplicar su regla de decision (1:4 o 1:10) segun la tolerancia de la cota.")

    pdf.output(ruta_final)
    return ruta_final