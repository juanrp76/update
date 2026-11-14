import json
import os
import requests
from google import genai

# Inicializar cliente de Google Gemini con la clave de los Secretos de GitHub
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def obtener_lote_masivo_api_bdns() -> list[dict]:
    """
    Realiza la petición al endpoint oficial de búsqueda de la BDNS 
    aprovechando el bloque máximo de 1000 convocatorias.
    """
    url = "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias/busqueda?vpd=GE&page=0&pageSize=1000&order=fechaRecepcion&direccion=desc"
    
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

    try:
        print("Consultando la API oficial de búsqueda de la BDNS (hasta 1000 registros)...")
        response = requests.get(url, headers=headers, cookies=cookies, timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            # Los resultados vienen en la propiedad 'content' según el esquema oficial
            items = data.get("content", [])
            print(f"¡Éxito! Se han obtenido {len(items)} convocatorias brutas de la BDNS.")
            return items
        else:
            print(f"Error en la respuesta de la API oficial: Código {response.status_code}")
    except Exception as e:
        print(f"Excepción al conectar con la API de la BDNS: {e}")
        
    return []

def procesar_con_gemini(item_bruto: dict) -> dict:
    """
    Usa Google Gemini para transformar los datos crudos de la BDNS 
    en el esquema JSON estricto requerido por la base de datos Room en Android.
    """
    numero_convocatoria = str(item_bruto.get("numeroConvocatoria", ""))
    descripcion = item_bruto.get("descripcion", "")
    nivel1 = item_bruto.get("nivel1", "Nacional")
    nivel2 = item_bruto.get("nivel2", "Organismo público")
    
    # Limpiamos comillas dobles para evitar romper el JSON del prompt
    descripcion_limpia = descripcion.replace('"', '').replace('\n', ' ')
    organismo_limpio = nivel2.replace('"', '')

    prompt = f"""
    Eres un experto en legislación y subvenciones en España. Analiza los datos de esta convocatoria oficial 
    y responde EXCLUSIVAMENTE con un JSON válido que tenga esta estructura exacta (sin texto extra ni formato markdown):
    {{
      "id": "{numero_convocatoria}",
      "titulo": "{descripcion_limpia}",
      "organismo": "{organismo_limpio}",
      "ccaa": "{nivel1}",
      "edad_minima": null,
      "edad_maxima": null,
      "ingresos_maximos_anuales": null,
      "situacion_laboral": ["empleado", "autonomo", "desempleado", "pensionista", "estudiante"],
      "estado_civil_permitido": ["Soltero/a", "Casado/a", "Separado/a o Divorciado/a", "Viudo/a"],
      "incompatible_con": [],
      "exige_estar_cobrando": [],
      "es_complementaria": false,
      "url_oficial": "https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatoria/{numero_convocatoria}"
    }}
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

if __name__ == "__main__":
    convocatorias_brutas = obtener_lote_masivo_api_bdns()
    
    lista_ayudas_finales = []
    
    # Procesamos un lote de seguridad por ejecución (ej: los primeros 40 más recientes) 
    # para asegurar un rendimiento óptimo en las GitHub Actions y respetar los límites de la API de IA.
    lote_a_procesar = convocatorias_brutas[:40]
    print(f"Procesando {len(lote_a_procesar)} convocatorias con Google Gemini...")
    
    for item in lote_a_procesar:
        try:
            ayuda_estructurada = procesar_con_gemini(item)
            lista_ayudas_finales.append(ayuda_estructurada)
        except Exception as e:
            print(f"Error procesando una ayuda individual: {e}")
            
    # Respaldo de emergencia por si la API oficial o la IA fallan puntualmente
    if not lista_ayudas_finales:
        print("Activando respaldo de emergencia...")
        lista_ayudas_finales = [{
            "id": "respaldo_emergencia",
            "titulo": "Ayuda de respaldo predeterminada",
            "organismo": "Ministerio",
            "ccaa": "Nacional",
            "edad_minima": None,
            "edad_maxima": None,
            "ingresos_maximos_anuales": None,
            "situacion_laboral": ["empleado", "autonomo", "desempleado"],
            "estado_civil_permitido": ["Soltero/a", "Casado/a"],
            "incompatible_con": [],
            "exige_estar_cobrando": [],
            "es_complementaria": False,
            "url_oficial": "https://www.pap.hacienda.gob.es"
        }]

    # Guardar el archivo definitivo que descargará Retrofit en tu app Android
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_ayudas_finales, f, ensure_ascii=False, indent=4)
        
    print(f"¡Éxito total! Archivo 'ayudas.json' generado con {len(lista_ayudas_finales)} ayudas listas para Android.")
