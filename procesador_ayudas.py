import json
import os
from google import genai

# Inicializar cliente con la nueva librería oficial de Google GenAI
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def procesar_texto_subvencion(texto_legal_crudo: str) -> dict:
    prompt = f"""
    Eres un experto en legislación y subvenciones en España. Analiza este texto legal 
    y responde EXCLUSIVAMENTE con un JSON válido que tenga esta estructura exacta (sin texto extra ni formato markdown):
    {{
      "id": "identificador_unico_minusculas",
      "titulo": "Título oficial",
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
      "url_oficial": "https://..."
    }}

    Texto legal:
    {texto_legal_crudo}
    """

    # Usamos el modelo actualizado que pide la API de Google
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    # Limpiar el texto devuelto por si incluye bloques de código markdown tipo ```json
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

if __name__ == "__main__":
    texto_ejemplo = "CONVOCATORIA BONO ALQUILER JOVEN 2026. Comunidad de Madrid. Menores de 35 años, ingresos < 24.318€."
    ayuda_procesada = procesar_texto_subvencion(texto_ejemplo)
    
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump([ayuda_procesada], f, ensure_ascii=False, indent=4)
    print("JSON generado correctamente con Gemini.")
