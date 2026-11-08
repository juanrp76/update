import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def procesar_texto_subvencion(texto_legal_crudo: str) -> dict:
    prompt = f"""
    Eres un asistente experto en legislación y subvenciones en España. 
    Analiza el siguiente texto de una convocatoria de subvención oficial y extrae un JSON estricto con esta estructura exacta:
    {{
      "id": "un_identificador_unico_corto_en_minusculas_y_sin_espacios",
      "titulo": "Título oficial de la ayuda",
      "organismo": "Nombre del organismo emisor",
      "ccaa": "Nombre de la Comunidad Autónoma o 'Nacional'",
      "edad_minima": null,
      "edad_maxima": null,
      "ingresos_maximos_anuales": null,
      "situacion_laboral": ["empleado", "autonomo", "desempleado", "pensionista", "estudiante"],
      "estado_civil_permitido": ["Soltero/a", "Casado/a", "Separado/a o Divorciado/a", "Viudo/a"],
      "incompatible_con": [],
      "exige_estar_cobrando": [],
      "es_complementaria": false,
      "url_oficial": "https://www.comunidad.madrid"
    }}

    Texto legal a analizar:
    {texto_legal_crudo}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices.message.content)

if __name__ == "__main__":
    # Simulación o lectura de nuevas leyes del BOE/BDNS
    texto_ejemplo = """
    CONVOCATORIA BONO ALQUILER JOVEN 2026. Comunidad de Madrid. 
    Dirigido a jóvenes menores de 35 años, con ingresos anuales inferiores a 24.318 euros.
    """
    
    # Procesamos con IA (puedes ampliar esto para leer varias leyes de una lista o API)
    ayuda_procesada = procesar_texto_subvencion(texto_ejemplo)
    
    # Creamos una lista con las ayudas
    lista_ayudas = [ayuda_procesada]
    
    # Guardamos el archivo ayudas.json que consumirá la app Android
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_ayudas, f, ensure_ascii=False, indent=4)
    print("Archivo ayudas.json generado correctamente.")
