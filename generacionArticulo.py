import sys
import json
import traceback
import os
from openai import OpenAI
from decouple import config
from datetime import datetime
import google.generativeai as genai
import datetime

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

def convertir_fecha_usuario(fecha_str):
    # Diccionario para convertir el número del mes a su nombre en español
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }

    # Convertir la cadena de fecha a un objeto datetime
    fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
    
    # Formatear la fecha en el formato deseado
    fecha_formateada = f"{fecha.day} de {meses[fecha.month]} del {fecha.year}"
    
    return fecha_formateada
    
def generar_nueva_noticia_gpt_noticias(noticias):
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    # Extrae el 'cuerpo' de cada noticia en la lista
    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    # Concatena los cuerpos de las noticias en un solo texto para usarlo como prompt
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    # Define un prompt para la generación de texto basado en las noticias procesadas
    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    # Realiza la llamada a la API de OpenAI para generar la nueva noticia
    try:
        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:noticias-bal:973thBIi",
            temperature=0.5,
            max_tokens=500,
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

def generar_nueva_noticia_gpt_base(noticias):
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    # Extrae el 'cuerpo' de cada noticia en la lista
    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    # Concatena los cuerpos de las noticias en un solo texto para usarlo como prompt
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    
    # Define un prompt para la generación de texto basado en las noticias procesadas
    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    # Realiza la llamada a la API de OpenAI para generar la nueva noticia
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=500,
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

def generar_nueva_noticia_gemini(noticias):
    genai.configure(api_key=config('GOOGLE_API_KEY'))

    safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
    ]
    
    # Extrae el 'cuerpo' de cada noticia en la lista
    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    # Concatena los cuerpos de las noticias en un solo texto para usarlo como prompt
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    context = "Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal."

    # Define un prompt para la generación de texto basado en las noticias procesadas
    prompt = f"{context} Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    model = genai.GenerativeModel(model_name="gemini-pro",
                              safety_settings=safety_settings)
    
    # Realiza la llamada a la API de Google para generar la nueva noticia
    try:
        response = model.generate_content(prompt)
        nueva_noticia = response.text

        return nueva_noticia
    
    except Exception as e:

        print(f"Error al generar nueva noticia con Google: {e}", file=sys.stderr)
        return ""
    
def generar_nuevo_titulo(nueva_noticia):
        client = OpenAI(api_key=config('OPENAI_API_KEY'), )
        prompt = f"Genera un título adecuado para esta noticia: {nueva_noticia}"

        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=60,
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

        modelo = noticias[0]['modelo']

        if modelo == "GPT-3.5-Base":
            nueva_noticia = generar_nueva_noticia_gpt_base(noticias)
        elif modelo == "GPT-3.5-News":
            nueva_noticia = generar_nueva_noticia_gpt_noticias(noticias)
        elif modelo == "Gemini":
            nueva_noticia = generar_nueva_noticia_gemini(noticias)
        else:
            nueva_noticia = ""

        nuevo_titulo = generar_nuevo_titulo(nueva_noticia)

        fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
        
        if nueva_noticia:
            print(json.dumps({"success": True, "data": nueva_noticia, "titulo": nuevo_titulo, "fecha": fecha, "modelo": modelo}))
        else:
            print(json.dumps({"success": False, "error": "No se pudo generar una nueva noticia"}))
        
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": "Error al deserializar el argumento JSON", "details": str(e)}), file=sys.stderr)
    except Exception as e:
        error_info = traceback.format_exc()
        print(json.dumps({"success": False, "error": "Error inesperado", "details": str(e), "trace": error_info}), file=sys.stderr)
