import json
import requests

def obtener_todas_las_ayudas_con_enlaces() -> list[dict]:
    """
    Descarga el listado masivo de la BDNS y construye automáticamente 
    los enlaces oficiales de consulta y tramitación para la app Android.
    """
    todas_las_convocatorias = []
    page = 0
    page_size = 1000
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es,es-ES;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.pap.hacienda.gob.es/bdnstrans/GE/eu/convocatorias',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36'
    }
    
    cookies = {
        'XSRF-TOKEN': 'fdcc2c56-6806-458b-8951-68c1c9724085'
    }

    print("Iniciando descarga masiva de convocatorias con enlaces oficiales...")

    while True:
        url = f"https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias/busqueda?vpd=GE&page={page}&pageSize={page_size}&order=fechaRecepcion&direccion=desc"
        
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=25)
            if response.status_code == 200:
                data = response.json()
                items = data.get("content", [])
                
                if not items:
                    break
                    
                todas_las_convocatorias.extend(items)
                print(f"-> Página {page}: cargadas {len(items)} ayudas. Acumulado: {len(todas_las_convocatorias)}")
                
                if len(items) < page_size:
                    break
                page += 1
            else:
                break
        except Exception as e:
            print(f"Error de conexión: {e}")
            break
            
    return todas_las_convocatorias

if __name__ == "__main__":
    brutas = obtener_todas_las_ayudas_con_enlaces()
    lista_final = []
    
    for item in brutas:
        num_convocatoria = str(item.get("numeroConvocatoria", ""))
        descripcion = item.get("descripcion", "")
        nivel1 = item.get("nivel1", "Nacional")
        nivel2 = item.get("nivel2", "Organismo público")
        
        # Construcción limpia de los enlaces oficiales
        url_detalle_bdns = f"https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/{num_convocatoria}"
        
        ayuda_mapeada = {
            "id": num_convocatoria,
            "titulo": descripcion,
            "organismo": nivel2,
            "ccaa": nivel1,
            "mrr": item.get("mrr", False),
            "fecha_recepcion": item.get("fechaRecepcion", ""),
            "fecha_inicio_solicitud": item.get("fechaInicioSolicitud", None),
            "fecha_fin_solicitud": item.get("fechaFinSolicitud", None),
            "url_oficial": url_detalle_bdns
        }
        lista_final.append(ayuda_mapeada)

    # Guardar JSON definitivo para Retrofit y Room en Android
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"¡Fichero 'ayudas.json' generado con éxito con {len(lista_final)} registros y enlaces oficiales integrados!")
