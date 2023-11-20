import sys
import json
from sentence_transformers import SentenceTransformer, util
import feedparser

def obtener_noticias_desde_fuentes(fuentes):
    noticias_descripciones = []
    for nombre_fuente, url_feed in fuentes:
        noticias = feedparser.parse(url_feed)
        for entrada in noticias.entries:
            titulo = entrada.title
            descripcion = entrada.description
            noticias_descripciones.append((titulo, descripcion))
    return noticias_descripciones

def main():
    consulta = sys.argv[1]  # Obtén la consulta desde los argumentos

    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    fuentes = [
        ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml?v=1"),
        ("Reforma", "https://www.reforma.com/rss/portada.xml"),
        ("Expansion", "https://expansion.mx/rss"),
    ]

    noticias = obtener_noticias_desde_fuentes(fuentes)

    sentences1 = [consulta]  # Usa la consulta aquí
    sentences2 = [noticia[1] for noticia in noticias]  # Solo las descripciones

    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    # Compute cosine-similarities
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # Create a list of tuples (consulta, titulo, descripcion, score)
    results = [(consulta, noticias[i][0], noticias[i][1], cosine_scores[0][i].item()) for i in range(len(noticias))]

    # Filtra los resultados por un umbral de similitud
    filtered_results = [result for result in results if result[3] >= 0.55]

    # Imprime los resultados filtrados
    print(json.dumps(filtered_results))

if __name__ == "__main__":
    main()