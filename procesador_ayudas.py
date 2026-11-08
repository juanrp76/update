import json
import os
from google import genai

# Inicializar cliente con la clave secreta de Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def obtener_catalogo_maestro() -> list[str]:
    """
    Catálogo maestro estructurado con ayudas reales en España 
    (vivienda, autónomos, empleo, pensiones contributivas y no contributivas, becas).
    """
    return [
        "CONVOCATORIA BONO ALQUILER JOVEN. Comunidad de Madrid. Menores de 35 años, ingresos anuales inferiores a 24.318 euros.",
        "AYUDAS DIGITALIZACION EMPRESAS Y AUTONOMOS (Kit Digital). Ministerio de Industria. Dirigido a autónomos y pymes en todo el territorio nacional.",
        "PRESTACION POR CESE DE ACTIVIDAD PARA TRABAJADORES AUTONOMOS. Seguridad Social. Ayuda dirigida exclusivamente a autónomos en situación de cese.",
        "PENSION NO CONTRIBUTIVA DE JUBILACION. IMSERSO. Mayores de 65 años con carencia de ingresos y rentas anuales inferiores a 7.250 euros.",
        "PENSION NO CONTRIBUTIVA DE INVALIDEZ. IMSERSO. Personas con discapacidad del 65% o más, sin recursos económicos suficientes.",
        "BECA ADQUISICION DE MATERIAL ESCOLAR Y LIBROS. Generalitat Valenciana. Familias con estudiantes en educación obligatoria con rentas bajas.",
        "AYUDAS A LA MOVILIDAD SOSTENIBLE (PLAN MOVES III). Ministerio para la Transición Ecológica. Particulares y autónomos para compra de vehículos eléctricos.",
        "SUBSIDIO POR DESEMPLEO PARA MAYORES DE 52 AÑOS. SEPE. Desempleados mayores de 52 años que hayan cotizado por desempleo.",
        "INGRESO MINIMO VITAL (IMV). Seguridad Social. Unidades de convivencia o personas solas en situación de vulnerabilidad económica.",
        "AYUDAS AL ALQUILER DE VIVIENDA PARA FAMILIAS NUMEROSAS. Generalitat de Catalunya. Familias numerosas con ingresos limitados."
    ]

def procesar_texto_subvencion(texto_legal_crudo: str) -> dict:
    """Envía el texto a Gemini para estructurarlo de forma estricta en JSON."""
    prompt = f"""
    Eres un experto en legislación y subvenciones en España. Analiza este texto legal 
    y responde EXCLUSIVAMENTE con un JSON válido que tenga esta estructura exacta (sin texto extra ni formato markdown):
    {{
      "id": "identificador_unico_minusculas_sin_espacios",
      "titulo": "Título oficial de la ayuda",
      "organismo": "Organismo emisor (ej: Comunidad de Madrid, Ministerio, IMSERSO, SEPE...)",
      "ccaa": "Comunidad Autónoma específica o 'Nacional'",
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
    
    # Limpiar marcas de markdown por seguridad
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

if __name__ == "__main__":
    print("Iniciando procesamiento de subvenciones con Gemini...")
    convocatorias_brutas = obtener_catalogo_maestro()
    
    lista_ayudas_totales = []
    print(f"Procesando {len(convocatorias_brutas)} convocatorias...")
    
    for texto in convocatorias_brutas:
        try:
            ayuda_json = procesar_texto_subvencion(texto)
            lista_ayudas_totales.append(ayuda_json)
        except Exception as e:
            print(f"Error procesando elemento: {e}")
    
    # Guardar el archivo JSON definitivo para la app Android
    with open("ayudas.json", "w", encoding="utf-8") as f:
        json.dump(lista_ayudas_totales, f, ensure_ascii=False, indent=4)
        
    print(f"¡Éxito! Archivo 'ayudas.json' generado con {len(lista_ayudas_totales)} subvenciones.")
