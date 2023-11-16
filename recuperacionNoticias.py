import sys
import json
from sentence_transformers import SentenceTransformer, util
import feedparser

def obtener_noticias_desde_fuentes(fuentes):
    noticias_descripciones = []
    for nombre_fuente, url_feed in fuentes:
        noticias = feedparser.parse(url_feed)
        for entrada in noticias.entries:
            descripcion = entrada.description
            noticias_descripciones.append(descripcion)
    return noticias_descripciones

def main():
    consulta = sys.argv[1] # Obtén la consulta desde los argumentos

    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    fuentes = [
        ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml?v=1"),
        ("Reforma", "https://www.reforma.com/rss/portada.xml"),
        ("Expansion", "https://expansion.mx/rss"),
    ]

    noticias_descripciones = obtener_noticias_desde_fuentes(fuentes)

    sentences1 = [consulta] # Usa la consulta aquí
    sentences2 = noticias_descripciones

    
    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    #Compute cosine-similarities
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # Create a list of tuples (sentence1, sentence2, score)
    results = [(sentences1[0], sentences2[i], cosine_scores[0][i].item()) for i in range(len(sentences2))]

    # Sort the results by score in descending order
    sorted_results = sorted(results, key=lambda x: x[2], reverse=True)

    # Devuelve solo los 3 primeros resultados
    print(json.dumps(sorted_results[:3]))

if __name__ == "__main__":
    main()
