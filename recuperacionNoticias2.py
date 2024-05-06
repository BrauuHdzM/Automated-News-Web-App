import sys
import json
from sentence_transformers import SentenceTransformer, util
import feedparser

def obtener_noticias_desde_fuentes(fuentes):
    noticias_descripciones = []
    for nombre_fuente, url_feed in fuentes:
        noticias = feedparser.parse(url_feed)
        for entrada in noticias.entries:
            if "opinion" not in entrada.link.lower():
                titulo = entrada.title
                descripcion = entrada.description
                fecha = entrada.published
                num_palabras_descripcion = len(descripcion.split())

                if num_palabras_descripcion > 5:
                    noticias_descripciones.append((nombre_fuente, titulo, fecha, descripcion))
    return noticias_descripciones


def main():
    json_string = sys.stdin.read()
                   
    consulta = json.loads(json_string)

    busqueda = consulta[0]['lugar'] + " " + consulta[0]['palabrasClave']

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

    sentences1 = [busqueda]  # Usa la consulta aquí
    sentences2 = [noticia[1] + " " + noticia[3] for noticia in noticias]

    lugar =  consulta[0]['lugar']

    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    results = [
        (noticias[i][0], noticias[i][1], noticias[i][2], noticias[i][3], cosine_scores[0][i].item(), i, lugar) 
        for i in range(len(noticias))
    ]

    filtered_results = [result for result in results if result[4] >= 0.55]

    print(json.dumps({"success": True, "resultados": filtered_results}))

if __name__ == "__main__":
    main()