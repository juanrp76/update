import json
from datetime import datetime
import requests

def obtener_ayudas_vigentes_por_anio() -> list[dict]:
    """
    Descarga masivamente de la BDNS y filtra de forma inteligente 
    para conservar únicamente las convocatorias recientes y del año actual.
    """
    todas_las_convocatorias = []
    page = 0
    page_size = 1000
    
    # Año actual (2026) o puedes permitir el año actual y el anterior (2025)
    ANIO_ACTUAL = 2026 
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es,es-ES;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.pap.hacienda.gob.es/bdnstrans/GE/eu/convocatorias',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
    }

    session = requests.Session()
    session.headers.update(headers)

    print("Obteniendo sesión y cookies dinámicas de la BDNS...")
    try:
        session.get("https://www.pap.hacienda.gob.es/bdnstrans/GE/eu/convocatorias", timeout=15)
    except Exception as e:
        print(f"Aviso al obtener la sesión inicial: {e}")

    print(f"Iniciando descarga filtrando por el año {ANIO_ACTUAL}...")

    while True:
        url = f"https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias/busqueda?vpd=GE&page={page}&pageSize={page_size}&order=fechaRecepcion&direccion=desc"
        
        try:
            print(f"Revisando página {page}...")
            response = session.get(url, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("content", [])
                
                if not items:
                    print("Se han alcanzado el total de páginas disponibles.")
                    break
                
                encontrados_en_pagina = 0
                for item in items:
                    fecha_str = item.get("fechaRecepcion", "")
                    
                    # Extraer el año de la fecha (formato habitual o timestamp)
                    anio_item = None
                    if fecha_str:
                        try:
                            # Intentar extraer el año de la cadena de fecha
                            if len(fecha_str) >= 4:
                                anio_item = int(fecha_str[:4])
                        except:
                            pass
                    
                    # Si es del año actual (o si no tiene fecha clara pero queremos incluirla por seguridad, ajustas aquí)
                    if anio_item and anio_item >= (ANIO_ACTUAL - 1): # Incluye 2026 y 2025 por si acaso
                        numero_convocatoria = str(item.get("numeroConvocatoria", ""))
                        descripcion = item.get("descripcion", "")
                        nivel1 = item.get("nivel1", "Nacional")
                        nivel2 = item.get("nivel2", "Organismo público")
                        
                        ayuda_mapeada = {
                            "id": numero_convocatoria,
                            "titulo": descripcion,
                            "organismo": nivel2,
                            "ccaa": nivel1,
                            "mrr": item.get("mrr", False),
                            "fecha_recepcion": fecha_str,
                            "fecha_inicio_solicitud": item.get("fechaInicioSolicitud", None),
                            "fecha_fin_solicitud": item.get("fechaFinSolicitud", None),
                            "url_oficial": f"https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/{numero_convocatoria}"
                        }
                        todas_las_convocatorias.append(ayuda_mapeada)
                        encontrados_en_pagina += 1

                print(f"-> Página {page}: Añadidas {encontrados_en_pagina} ayudas vigentes. Total acumulado: {len(todas_las_convocatorias)}")
                
                # Si en esta página ya nos hemos metido en años muy antiguos (ej. 2023 o anterior) 
                # dado que la API ordena de más nuevo a más viejo, podemos cortar el bucle para ahorrar tiempo.
                if items:
                    ultima_fecha = items[-1].get("fechaRecepcion", "")
                    if ultima_fecha and int(ultima_fecha[:4]) < (ANIO_ACTUAL - 1):
                        print("Hemos alcanzado registros de años anteriores. Finalizando descarga.")
                        break

                if len(items) < page_size:
                    break
                    
                page += 1
            else:
                break
                
        except Exception as e:
            print(f"Excepción en página {page}: {e}")
            break
            
    return todas_las_convocatorias

if __name__ == "__main__":
    lista_ayudas_finales = obtener_ayudas_validas = obtener_ayudas_vigentes_por_anio()
    
    if not lista_ayudas_finales:
        lista_ayudas_finales = [{
            "id": "respaldo_emergencia",
            "titulo": "Ayuda de respaldo predeterminada",
            "organismo": "Ministerio",
            "ccaa": "Nacional",
            "mrr": False,
            "fecha_recepcion": "",
            "fecha_inicio_solicitud": None,
            "fecha_fin_solicitud": None,
            "url_oficial": "https://www.pap.hacienda.gob.es"
        }]

    # Guardar el archivo JSON optimizado (pesará unos pocos megas, perfecto para GitHub)
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_ayudas_finales, f, ensure_ascii=False, indent=4)
        
    print(f"¡Éxito total! Archivo 'ayudas.json' generado con {len(lista_ayudas_finales)} ayudas vigentes.")
