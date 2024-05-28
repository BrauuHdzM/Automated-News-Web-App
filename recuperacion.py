import sys
import json
from openai import OpenAI
from decouple import config
import feedparser
import numpy as np
import certifi
import ssl
import urllib.request

client = OpenAI(api_key=config('OPENAI_API_KEY'))

# Configurar SSL para usar los certificados de certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

def obtener_noticias_desde_fuentes(fuentes):
    noticias_descripciones = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    for nombre_fuente, url_feed in fuentes:
        try:
            req = urllib.request.Request(url_feed, headers=headers)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                data = response.read()
                noticias = feedparser.parse(data)
                print(f"Procesando feed: {nombre_fuente} - {url_feed}")
                if noticias.bozo:
                    print(f"Error al procesar el feed: {url_feed}")
                    print(f"Bozo exception: {noticias.bozo_exception}")
                    continue
                print(f"Noticias crudas: {noticias}")
                if 'entries' not in noticias or len(noticias.entries) == 0:
                    print(f"No se encontraron entradas en el feed: {url_feed}")
                    continue
                for entrada in noticias.entries:
                    if "opinion" not in entrada.link.lower():
                        titulo = entrada.title
                        descripcion = entrada.description
                        fecha = entrada.published if 'published' in entrada else "Fecha no disponible"
                        num_palabras_descripcion = len(descripcion.split())
                        if num_palabras_descripcion > 5:
                            noticias_descripciones.append((nombre_fuente, titulo, fecha, descripcion))
                        else:
                            print(f"Descripción demasiado corta en: {titulo}")
        except Exception as e:
            print(f"Error al procesar la fuente {nombre_fuente} con URL {url_feed}: {e}")
    return noticias_descripciones

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def cosine_similarity(v1, v2):
    """Calcular la similitud del coseno entre dos vectores."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():         
    consulta = "mexico"
    busqueda = "mexico amlo"
    print("Consulta de búsqueda:", busqueda)
    
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
        ("Expansion", "https://expansion.mx/rss"),
    ]

    noticias = obtener_noticias_desde_fuentes(fuentes)
    print("Noticias recuperadas:", len(noticias))
    sentences1 = [busqueda]
    sentences2 = [noticia[1] + " " + noticia[3] for noticia in noticias]

    lugar = "mexico"
    fecha = "2024-05-28"

    # Genera embeddings para la consulta y las noticias
    embeddings1 = client.embeddings.create(
        input=sentences1,
        model="text-embedding-3-small"
    ).data[0].embedding

    embeddings2 = [get_embedding(sentence, model="text-embedding-3-small") for sentence in sentences2]

    # Calcula similitud del coseno
    cosine_scores = [cosine_similarity(embeddings1, embedding) for embedding in embeddings2]

    results = [
        (noticias[i][0], noticias[i][1], noticias[i][2], noticias[i][3], cosine_scores[i], i, lugar, fecha) 
        for i in range(len(noticias))
    ]

    print("Resultados obtenidos:", results)
    filtered_results = [result for result in results if result[4] >= 0.55]

    print(json.dumps({"success": True, "resultados": filtered_results}, indent=4))

if __name__ == "__main__":
    main()
