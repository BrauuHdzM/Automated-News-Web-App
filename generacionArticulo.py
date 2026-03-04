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

        fecha_parseada = datetime.strptime(fecha_original[:25], "%a, %d %b %Y %H:%M:%S")

        mes_en_ingles = fecha_parseada.strftime("%B")
        mes_en_espanol = meses_en_espanol.get(mes_en_ingles, "mes desconocido")

        return fecha_parseada.strftime(f"%d de {mes_en_espanol} del %Y")
    except ValueError as e:
        return f"Formato de fecha incorrecto: {e}"
    except KeyError as e:
        return f"Error en el diccionario de meses: {e}"

def convertir_fecha_usuario(fecha_str):
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }

    fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
    
    fecha_formateada = f"{fecha.day} de {meses[fecha.month]} del {fecha.year}"
    
    return fecha_formateada
    
def generar_nueva_noticia_gpt_noticias(noticias, contenido_extra=""):
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    if contenido_extra:
        prompt += f" Información adicional proporcionada por el usuario: {contenido_extra}"
    
    try:
        completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal:noticias-bal:973thBIi",
            temperature=1.0,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": "Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal."},
                {"role": "user", "content": f"{prompt}"}
            ]
            )
        
        nueva_noticia = completion.choices[0].message.content

        completion2 = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.0,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": "Tu tarea es ayudar a parafrasear y mejorar un poco la redacción del texto que se te ofrece."},
                {"role": "user", "content": f"Con el siguiente artículo de noticia generado por un modelo de lenguaje, mejora la redacción y parafrasea el texto para que suene más natural: {nueva_noticia}, no inventes informacion adicional ni inventes datos que no estén expresamente mencionados en el texto."}
            ]
            )
        return completion2.choices[0].message.content
    
    except Exception as e:

        print(f"Error al generar nueva noticia con OpenAI: {e}", file=sys.stderr)
        return ""


def generar_nueva_noticia_gpt_base(noticias, contenido_extra=""):
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    if contenido_extra:
        prompt += f" Información adicional proporcionada por el usuario: {contenido_extra}"
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=1024,
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

def generar_nueva_noticia_gemini(noticias, contenido_extra=""):
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    cuerpos_noticias = [noticia['cuerpo'] for noticia in noticias]
    
    texto_noticias = ' '.join(cuerpos_noticias)
    
    fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
    lugar = noticias[0]['lugar']

    prompt = f"Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
    
    if contenido_extra:
        prompt += f" Información adicional proporcionada por el usuario: {contenido_extra}"
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
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

def generar_noticia_solo_contenido_extra(contenido_extra, modelo, fecha_usuario=None):
    """Genera un artículo basándose únicamente en el contenido extra proporcionado por el usuario."""
    client = OpenAI(api_key=config('OPENAI_API_KEY'), )

    fecha = convertir_fecha_usuario(fecha_usuario) if fecha_usuario else "Fecha no especificada"

    prompt = f"Crea un artículo de noticias con la siguiente información proporcionada por el usuario: {contenido_extra}. Fecha: {fecha}."

    model_name = "gpt-4o-mini"
    if modelo == "GPT-3.5-Base":
        model_name = "gpt-3.5-turbo"
    elif modelo == "GPT-3.5-News":
        model_name = "ft:gpt-3.5-turbo-0125:personal:noticias-bal:973thBIi"

    try:
        completion = client.chat.completions.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": "Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal."},
                {"role": "user", "content": f"{prompt}"}
            ]
        )
        
        nueva_noticia = completion.choices[0].message.content

        if modelo == "GPT-3.5-News":
            completion2 = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=1.0,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": "Tu tarea es ayudar a parafrasear y mejorar un poco la redacción del texto que se te ofrece."},
                    {"role": "user", "content": f"Con el siguiente artículo de noticia generado por un modelo de lenguaje, mejora la redacción y parafrasea el texto para que suene más natural: {nueva_noticia}, no inventes informacion adicional ni inventes datos que no estén expresamente mencionados en el texto."}
                ]
            )
            return completion2.choices[0].message.content

        return nueva_noticia
    
    except Exception as e:
        print(f"Error al generar nueva noticia con OpenAI: {e}", file=sys.stderr)
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
        payload = json.loads(entrada_json)

        noticias = payload.get('noticiasSeleccionadas', [])
        contenido_extra = payload.get('contenidoExtra', '')
        modelo_global = payload.get('modelo', 'Gemini')
        fecha_usuario_global = payload.get('fechaUsuario', None)

        if len(noticias) == 0 and contenido_extra:
            nueva_noticia = generar_noticia_solo_contenido_extra(contenido_extra, modelo_global, fecha_usuario_global)
            medios_usados = "Artículo generado a partir de contenido proporcionado por el usuario."
            nueva_noticia = nueva_noticia + "<br><br>" + medios_usados
            nuevo_titulo = generar_nuevo_titulo(nueva_noticia)
            fecha = convertir_fecha_usuario(fecha_usuario_global) if fecha_usuario_global else "Fecha no especificada"

            if nueva_noticia:
                print(json.dumps({"success": True, "data": nueva_noticia, "titulo": nuevo_titulo, "fecha": fecha, "modelo": modelo_global}))
            else:
                print(json.dumps({"success": False, "error": "No se pudo generar una nueva noticia"}))

        elif len(noticias) > 0:
            modelo = noticias[0]['modelo']

            if modelo == "GPT-3.5-Base":
                nueva_noticia = generar_nueva_noticia_gpt_base(noticias, contenido_extra)
            elif modelo == "GPT-3.5-News":
                nueva_noticia = generar_nueva_noticia_gpt_noticias(noticias, contenido_extra)
            elif modelo == "Gemini":
                nueva_noticia = generar_nueva_noticia_gemini(noticias, contenido_extra)
            else:
                nueva_noticia = ""

            medios = list(set([noticia['medio'] for noticia in noticias]))
            medios_usados = "Realizado con información de: " + ", ".join(medios)
            
            if contenido_extra:
                medios_usados += " | Complementado con contenido del usuario."

            nueva_noticia = nueva_noticia + "<br><br>" + medios_usados

            nuevo_titulo = generar_nuevo_titulo(nueva_noticia)

            fecha = convertir_fecha_usuario(noticias[0]['fechaUsuario'])
            
            if nueva_noticia:
                print(json.dumps({"success": True, "data": nueva_noticia, "titulo": nuevo_titulo, "fecha": fecha, "modelo": modelo}))
            else:
                print(json.dumps({"success": False, "error": "No se pudo generar una nueva noticia"}))
        else:
            print(json.dumps({"success": False, "error": "No se proporcionaron noticias ni contenido extra"}))
        
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": "Error al deserializar el argumento JSON", "details": str(e)}), file=sys.stderr)
    except Exception as e:
        error_info = traceback.format_exc()
        print(json.dumps({"success": False, "error": "Error inesperado", "details": str(e), "trace": error_info}), file=sys.stderr)