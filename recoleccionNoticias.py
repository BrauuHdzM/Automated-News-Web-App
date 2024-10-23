import feedparser
import csv
from html import unescape

def obtener_noticias_desde_fuentes(fuentes, archivo_csv):
    with open(archivo_csv, 'a', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for nombre_fuente, url_feed in fuentes:
            noticias = feedparser.parse(url_feed)
            for entrada in noticias.entries:
                titulo = entrada.title
                enlace = entrada.link
                fecha = entrada.published
                descripcion = entrada.description

                row = [f'{titulo}', f'{enlace}', f'{fecha}', f'{descripcion}']
                csv_writer.writerow(row)

                print("Fuente:", nombre_fuente)
                print("Título:", titulo)
                print("Enlace:", enlace)
                print("Fecha de publicación:", fecha)
                print("Descripción:", descripcion)
                print("\n")

"""### La Jornada, Reforma, Expansion"""

fuentes = [
        ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml?v=1"),
        ("Reforma", "https://www.reforma.com/rss/portada.xml"),
        ("Reforma", "https://www.reforma.com/rss/internacional.xml"),
        ("Reforma", "https://www.reforma.com/rss/cancha.xml"),
        ("Reforma", "https://www.reforma.com/rss/justicia.xml"),
        ("Reforma", "https://www.reforma.com/rss/ciudad.xml"),
        ("Reforma", "https://www.reforma.com/rss/negocios.xml"),
        ("Reforma", "https://www.reforma.com/rss/estados.xml"),
        ("Reforma", "https://www.reforma.com/rss/nacional.xml"),
        ("Reforma", "https://www.reforma.com/rss/ciencia.xml"),
        ("Expansion", "https://expansion.mx/rss"),
        ("El Financiero", "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/?outputType=xml")
    ]

archivo_csv = "noticias.csv"
obtener_noticias_desde_fuentes(fuentes, archivo_csv)

with open('noticias.csv', 'r') as archivo_csv:
    lector = csv.reader(archivo_csv, delimiter=",")
    primera_fila = next(lector)

    print(primera_fila)

import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split

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

# Cargar el dataset
file_path = '/work/noticias.csv'
data = pd.read_csv(file_path)

# Limpieza de datos
data_clean = data.dropna()
data_clean = data_clean[data_clean['Contenido'].apply(lambda x: len(x.split()) > 6)]

data_clean['Fecha'] = data_clean['Fecha'].apply(convertir_fecha_gmt_a_espanol)

# Dividir el dataset
X = data_clean[['Título', 'Vínculo', 'Fecha', 'Contenido']]
X_train, X_test = train_test_split(X, test_size=0.1, random_state=42)

# Guardar los conjuntos en archivos CSV
X_train.to_csv('/work/train.csv', index=False)
X_test.to_csv('/work/test.csv', index=False)

import feedparser
import sys
import json
from sentence_transformers import SentenceTransformer, util

def obtener_noticias_desde_fuentes(fuentes):
    noticias_descripciones = []
    noticias_vistas = set()  # Conjunto para almacenar combinaciones únicas de título y descripción

    for nombre_fuente, url_feed in fuentes:
        noticias = feedparser.parse(url_feed)
        for entrada in noticias.entries:
            titulo = entrada.title
            descripcion = entrada.description
            fecha = entrada.published

            # Verificar si la noticia ya fue procesada
            identificador_noticia = titulo + descripcion
            if identificador_noticia not in noticias_vistas:
                noticias_vistas.add(identificador_noticia)
                noticias_descripciones.append((nombre_fuente, titulo, fecha, descripcion))

    return noticias_descripciones

def main():
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    fuentes = [
        ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml?v=1"),
        ("Reforma", "https://www.reforma.com/rss/portada.xml"),
        ("Reforma", "https://www.reforma.com/rss/internacional.xml"),
        ("Reforma", "https://www.reforma.com/rss/cancha.xml"),
        ("Reforma", "https://www.reforma.com/rss/justicia.xml"),
        ("Reforma", "https://www.reforma.com/rss/ciudad.xml"),
        ("Reforma", "https://www.reforma.com/rss/negocios.xml"),
        ("Reforma", "https://www.reforma.com/rss/estados.xml"),
        ("Reforma", "https://www.reforma.com/rss/nacional.xml"),
        ("Reforma", "https://www.reforma.com/rss/ciencia.xml"),
        ("Expansion", "https://expansion.mx/rss"),
    ]

    noticias = obtener_noticias_desde_fuentes(fuentes)

    if not noticias:
        print("No hay noticias disponibles para procesar.")
        return

    descripciones_noticias = [noticia[1] + " " + noticia[3] for noticia in noticias]

    embeddings = model.encode(descripciones_noticias, convert_to_tensor=True)

    cosine_scores = util.pytorch_cos_sim(embeddings, embeddings)

    pares_similares = []
    for i in range(len(cosine_scores)-1):
            for j in range(i+1, len(cosine_scores)):
                similitud = cosine_scores[i][j].item()
                if 0.95 > similitud >= 0.60:  # Excluir pares con similitud muy alta
                    pares_similares.append((i, j, similitud))

    pares_similares = sorted(pares_similares, key=lambda x: x[2], reverse=True)[:20]

    resultados_finales = []
    for par in pares_similares:
        idx1, idx2, score = par
        resultados_finales.append({
            "Noticia 1": noticias[idx1],
            "Noticia 2": noticias[idx2],
            "Similitud": score
        })

    print(json.dumps(resultados_finales, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    main()