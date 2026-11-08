import json
import os
import requests
from google import genai

# Inicializar cliente con la clave de Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def obtener_convocatorias_bdns() -> list[str]:
    """
    Consulta la API pública de la Base de Datos Nacional de Subvenciones (BDNS)
    para extraer un listado amplio de convocatorias recientes en España.
    """
    textos_legales = []
    try:
        # Endpoint público del buscador de la BDNS para extraer convocatorias recientes
        url_bdns = "https://www.infosubvenciones.es/bdnstrans/Ares/es/api/convocatorias/ultimas"
        
        response = requests.get(url_bdns, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # La API suele devolver un listado u objeto con las convocatorias
            conves = data.get("convocatorias", []) if isinstance(data, dict) else data
            
            # Procesamos un buen lote (por ejemplo, las últimas 30 o 50 disponibles)
            for conv in conves[:50]:
                titulo = conv.get('titulo', '')
                beneficiarios = conv.get('beneficiarios', '')
                extracto = conv.get('extracto', '')
                
                texto_crudo = f"Título: {titulo}. Beneficiarios: {beneficiarios}. Extracto: {extracto}"
                if len(texto_crudo.strip()) > 20:
                    textos_legales.append(texto_crudo)
                    
            print(f"Se han obtenido {len(textos_legales)} convocatorias desde la BDNS.")
        else:
            print(f"Respuesta no exitosa de la BDNS: {response.status_code}")
            
    except Exception as e:
        print(f"Error al conectar con la API de la BDNS: {e}")
        
    return textos_legales

def procesar_texto_subvencion(texto_legal_crudo: str) -> dict:
    """Envía el texto legal crudo a Gemini para limpiarlo y transformarlo en el esquema JSON estricto."""
    prompt = f"""
    Eres un experto en legislación y subvenciones en España. Analiza este texto legal 
    y responde EXCLUSIVAMENTE con un JSON válido que tenga esta estructura exacta (sin texto extra ni formato markdown):
    {{
      "id": "identificador_unico_minusculas_sin_espacios",
      "titulo": "Título oficial de la ayuda",
      "organismo": "Organismo emisor (ej: Comunidad de Madrid, Ministerio...)",
      "ccaa": "Comunidad Autónoma o Nacional",
      "edad_minima": null,
      "edad_maxima": null,
      "ingresos_maximos_anuales": null,
      "situacion_laboral": ["empleado", "autonomo", "desempleado", "pensionista", "estudiante"],
      "estado_civil_permitido": ["Soltero/a", "Casado/a", "Separado/a o Divorciado/a", "Viudo/a"],
      "incompatible_con": [],
      "exige_estar_cobrando": [],
      "es_complementaria": false,
      "url_oficial": "https://..."
    }}

    Texto legal a analizar:
    {texto_legal_crudo}
    """

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    # Limpiar posibles marcas de markdown del modelo
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

if __name__ == "__main__":
    print("Iniciando la recogida masiva de convocatorias...")
    convocatorias_brutas = obtener_convocatorias_bdns()
    
    lista_ayudas_totales = []
    print(f"Procesando {len(convocatorias_brutas)} convocatorias con Google Gemini...")
    
    for texto in convocatorias_brutas:
        try:
            ayuda_json = procesar_texto_subvencion(texto)
            lista_ayudas_totales.append(ayuda_json)
        except Exception as e:
            print(f"Error procesando una ayuda individual: {e}")
    
    # Guardar el archivo JSON definitivo con todas las ayudas dinámicas
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_ayudas_totales, f, ensure_ascii=False, indent=4)
        
    print(f"¡Éxito! Archivo 'ayudas.json' actualizado con {len(lista_ayudas_totales)} subvenciones reales.")
