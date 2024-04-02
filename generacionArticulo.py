import sys
import json
import traceback
import os
from openai import OpenAI
from decouple import config


client = OpenAI(
  api_key=config('OPENAI_API_KEY'), 
)

def generar_nueva_noticia(noticias):
    # Extrae el 'cuerpo' de cada noticia en la lista
    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    # Concatena los cuerpos de las noticias en un solo texto para usarlo como prompt
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = noticias[0]['fecha']
    # Define un prompt para la generación de texto basado en las noticias procesadas
    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}"
    
    # Realiza la llamada a la API de OpenAI para generar la nueva noticia
    try:
        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:noticias-bal:973thBIi",
            messages=[
                {"role": "system", "content": "Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal."},
                {"role": "user", "content": f"{prompt}"}
            ]
            )
        
        nueva_noticia = completion.choices[0].message.content
        return nueva_noticia
    
    except Exception as e:

        print(f"Error al generar nueva noticia con OpenAI: {e}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    try:
        entrada_json = sys.stdin.read()
        noticias = json.loads(entrada_json)
        
        # Aquí podrías procesar las noticias individualmente si es necesario
        # Por simplicidad, se asume que 'noticias' es una lista de textos de noticias
        nueva_noticia = generar_nueva_noticia(noticias)
        
        if nueva_noticia:
            print(json.dumps({"success": True, "data": nueva_noticia}))
        else:
            print(json.dumps({"success": False, "error": "No se pudo generar una nueva noticia"}))
        
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": "Error al deserializar el argumento JSON", "details": str(e)}), file=sys.stderr)
    except Exception as e:
        error_info = traceback.format_exc()
        print(json.dumps({"success": False, "error": "Error inesperado", "details": str(e), "trace": error_info}), file=sys.stderr)
