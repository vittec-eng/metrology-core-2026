import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

DATA_PATH = "data"
SOURCES = {
    "patrones": os.path.join(DATA_PATH, "patrones"),
    "instrumentos": os.path.join(DATA_PATH, "instrumentos")
}

def calcular_vencimiento(fecha_str, meses):
    try:
        # Validar que fecha_str no sea None o vacío
        if not fecha_str or fecha_str == 'N/A' or fecha_str == 'None':
            return "9999-12-31" # Para que los sin fecha queden al final
        
        # Tomamos los primeros 10 caracteres por si viene con hora (como en MI-0001)
        fecha_base = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
        return (fecha_base + relativedelta(months=meses)).strftime("%Y-%m-%d")
    except:
        return "9999-12-31" # Para que los sin fecha queden al final

def generar_indices():
    for rama, carpeta in SOURCES.items():
        lista_index = []
        if not os.path.exists(carpeta): continue

        for root, _, files in os.walk(carpeta):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        d = json.load(f)
                        
                        # --- FILTRO DE ESTADO ---
                        # Si el estado es 'obsoleto', saltamos este archivo y no se indexa
                        if d.get("estado") == "obsoleto":
                            continue
                        
                        vencimiento = calcular_vencimiento(
                            d.get("fecha_ultima_calibracion"), 
                            d.get("periodicidad_meses", 12)
                        )

                        lista_index.append({
                            "id": d.get("id"),
                            "descripcion": d.get("descripcion"),
                            "vencimiento": vencimiento,
                            "familia": d.get("familia"),
                            "path": os.path.join(root, file)
                        })
        # Ordenar por fecha de vencimiento (el que antes caduca, primero)
        lista_index.sort(key=lambda x: x["vencimiento"])

        with open(os.path.join(DATA_PATH, f"index_{rama}.json"), "w", encoding='utf-8') as f:
            json.dump(lista_index, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generar_indices()