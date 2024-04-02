import sys
import json
import traceback
import os
from openai import OpenAI
from decouple import config
from datetime import datetime

client = OpenAI(
  api_key=config('OPENAI_API_KEY'), 
)

def convertir_fecha_gmt_a_espanol(fecha_original):
    try:
        # Diccionario para traducir los nombres de los meses al español
        meses_en_espanol = {
            "January": "enero",
            "February": "febrero",
            "March": "marzo",
            "April": "abril",
            "May": "mayo",
            "June": "junio",
            "July": "julio",
            "August": "agosto",
            "September": "septiembre",
            "October": "octubre",
            "November": "noviembre",
            "December": "diciembre"
        }

        # Ajustar el formato para manejar zonas horarias con desplazamiento
        fecha_parseada = datetime.strptime(fecha_original[:25], "%a, %d %b %Y %H:%M:%S")

        # Obtener el nombre del mes en inglés y traducir al español
        mes_en_ingles = fecha_parseada.strftime("%B")
        mes_en_espanol = meses_en_espanol.get(mes_en_ingles, "mes desconocido")

        # Formato final en español
        return fecha_parseada.strftime(f"%d de {mes_en_espanol} del %Y")
    except ValueError as e:
        # Manejar el error si el formato de fecha_original no es el esperado
        return f"Formato de fecha incorrecto: {e}"
    except KeyError as e:
        # Manejar el error si el mes no se encuentra en el diccionario
        return f"Error en el diccionario de meses: {e}"
    
def generar_nueva_noticia(noticias):
    # Extrae el 'cuerpo' de cada noticia en la lista
    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    # Concatena los cuerpos de las noticias en un solo texto para usarlo como prompt
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_gmt_a_espanol(noticias[0]['fecha'])
    lugar = noticias[0]['lugar']

    # Define un prompt para la generación de texto basado en las noticias procesadas
    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
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
    
def generar_nuevo_titulo(nueva_noticia):
        prompt = f"Genera un título adecuado para esta noticia: {nueva_noticia}"

        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=30,
                temperature=0.5,
                messages=[
                    {"role": "system", "content": "Tu tarea es escribir un título adecuado para la noticia que se te presenta."},
                    {"role": "user", "content": f"{prompt}"}
                ]

            )
            
            nuevo_titulo = completion.choices[0].message.content
            return nuevo_titulo
        
        except Exception as e:
            print(f"Error al generar nuevo título con OpenAI: {e}", file=sys.stderr)
            return ""

if __name__ == "__main__":
    try:
        entrada_json = sys.stdin.read()
        noticias = json.loads(entrada_json)
        
        # Aquí podrías procesar las noticias individualmente si es necesario
        # Por simplicidad, se asume que 'noticias' es una lista de textos de noticias
        nueva_noticia = generar_nueva_noticia(noticias)

        nuevo_titulo = generar_nuevo_titulo(nueva_noticia)

        fecha = convertir_fecha_gmt_a_espanol(noticias[0]['fecha'])
        
        if nueva_noticia:
            print(json.dumps({"success": True, "data": nueva_noticia, "titulo": nuevo_titulo, "fecha": fecha}))
        else:
            print(json.dumps({"success": False, "error": "No se pudo generar una nueva noticia"}))
        
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": "Error al deserializar el argumento JSON", "details": str(e)}), file=sys.stderr)
    except Exception as e:
        error_info = traceback.format_exc()
        print(json.dumps({"success": False, "error": "Error inesperado", "details": str(e), "trace": error_info}), file=sys.stderr)
