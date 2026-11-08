import json
import os
import requests
from google import genai

# Inicializar cliente de Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def obtener_convocatorias_api_oficial() -> list[str]:
    """
    Consume directamente el endpoint oficial /convocatorias/ultimas de la BDNS
    visto en su documentación técnica para extraer convocatorias reales.
    """
    textos_legales = []
    try:
        # Endpoint oficial que devuelve las últimas convocatorias registradas
        url_api = "https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/ultimas"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url_api, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Dependiendo de si devuelve un array directo o un objeto con 'content'
            items = data.get("content", data) if isinstance(data, dict) else data
            
            for item in items[:30]: # Cogemos un lote fresco de las últimas
                descripcion = item.get("descripcion", "")
                nivel1 = item.get("nivel1", "Nacional")
                nivel2 = item.get("nivel2", "")
                
                texto_crudo = f"Ámbito: {nivel1}. Organismo: {nivel2}. Descripción: {descripcion}"
                if len(texto_crudo.strip()) > 30:
                    textos_legales.append(texto_crudo)
                    
            print(f"¡Éxito! Obtenidas {len(textos_legales)} convocatorias de la API oficial.")
            
    except Exception as e:
        print(f"Aviso al consultar la API oficial de la BDNS: {e}")

    # Respaldo por si hay restricciones puntuales de red en los servidores de GitHub
    if not textos_legales:
        print("Activando respaldo de seguridad...")
        textos_legales = [
            "Ámbito: NACIONAL. Organismo: MINISTERIO DE INDUSTRIA. Descripción: Ayudas del programa Kit Digital para digitalización de autónomos y pymes."
        ]
        
    return textos_legales

def procesar_con_gemini(texto_crudo: str) -> dict:
    """Envía el texto oficial a Gemini para estructurarlo en el JSON que leerá Android."""
    prompt = f"""
    Analiza esta convocatoria oficial de la BDNS y responde EXCLUSIVAMENTE con un JSON válido con esta estructura exacta (sin formato markdown ni texto extra):
    {{
      "id": "identificador_unico_minusculas_sin_espacios",
      "titulo": "Título o descripción resumida de la ayuda",
      "organismo": "Organismo emisor",
      "ccaa": "Comunidad Autónoma o Nacional",
      "edad_minima": null,
      "edad_maxima": null,
      "ingresos_maximos_anuales": null,
      "situacion_laboral": ["empleado", "autonomo", "desempleado", "pensionista", "estudiante"],
      "estado_civil_permitido": ["Soltero/a", "Casado/a", "Separado/a o Divorciado/a", "Viudo/a"],
      "incompatible_con": [],
      "exige_estar_cobrando": [],
      "es_complementaria": false,
      "url_oficial": "https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias"
    }}

    Texto a analizar:
    {texto_crudo}
    """

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

if __name__ == "__main__":
    print("Iniciando sincronización con la API oficial de la BDNS...")
    brutas = obtener_convocatorias_api_oficial()
    
    lista_final = []
    for texto in brutas:
        try:
            item_json = procesar_con_gemini(texto)
            lista_final.append(item_json)
        except Exception as e:
            print(f"Error procesando item con IA: {e}")
            
    # Guardamos el archivo final que consumirá Retrofit en la app Android
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)
        
    print(f"¡Listo! 'ayudas.json' actualizado con {len(lista_final)} registros oficiales.")
