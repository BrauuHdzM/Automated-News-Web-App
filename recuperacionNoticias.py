import sys
import json
import ssl
import urllib.request
import feedparser
import numpy as np
import certifi
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from decouple import config

client = OpenAI(api_key=config('OPENAI_API_KEY'))
THRESHOLD = config('SIMILARITY_THRESHOLD', default=0.55, cast=float)
ssl_context = ssl.create_default_context(cafile=certifi.where())

def descargar_una_fuente(fuente):
    nombre_fuente, url_feed = fuente
    noticias_fuente = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            data = response.read()
            feed = feedparser.parse(data)
            for entrada in feed.entries:
                if "opinion" not in entrada.link.lower():
                    titulo = entrada.get('title', '')
                    descripcion = entrada.get('description', '')
                    fecha = entrada.get('published', "Fecha no disponible")
                    
                    if len(descripcion.split()) > 5:
                        noticias_fuente.append((nombre_fuente, titulo, fecha, descripcion))
    except Exception as e:
        sys.stderr.write(f"Error en {nombre_fuente}: {e}\n")
    
    return noticias_fuente

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            return
        consulta_json = json.loads(input_data)
        consulta = consulta_json[0]

        busqueda = f"{consulta['lugar']} {consulta['palabrasClave']}"
        lugar = consulta['lugar']
        fecha_req = consulta['fecha']

        fuentes = [
            ("La Jornada", "https://www.jornada.com.mx/rss/edicion.xml?v=1"),
            ("Expansion", "https://expansion.mx/rss"),
            ("Reforma Portada", "https://www.reforma.com/rss/portada.xml"),
            ("Reforma Inter", "https://www.reforma.com/rss/internacional.xml"),
            ("Reforma Justicia", "https://www.reforma.com/rss/justicia.xml"),
            ("Reforma Ciudad", "https://www.reforma.com/rss/ciudad.xml"),
            ("Reforma Nacional", "https://www.reforma.com/rss/nacional.xml")
        ]

        with ThreadPoolExecutor(max_workers=len(fuentes)) as executor:
            resultados_listas = list(executor.map(descargar_una_fuente, fuentes))
        
        noticias = [n for sublista in resultados_listas for n in sublista]

        if not noticias:
            print(json.dumps({"success": True, "resultados": []}))
            return

        textos_noticias = [f"{n[1]} {n[3]}" for n in noticias]
        
        res_embeddings = client.embeddings.create(
            input=[busqueda] + textos_noticias,
            model="text-embedding-3-small"
        )
        
        emb_consulta = np.array(res_embeddings.data[0].embedding)
        embs_noticias = [np.array(item.embedding) for item in res_embeddings.data[1:]]

        filtered_results = []
        for i, emb_n in enumerate(embs_noticias):
            score = cosine_similarity(emb_consulta, emb_n)
            
            if score >= THRESHOLD:
                filtered_results.append([
                    noticias[i][0],    # 0: fuente
                    noticias[i][1],    # 1: titulo
                    noticias[i][2],    # 2: fecha
                    noticias[i][3],    # 3: descripcion
                    round(float(score), 4), # 4: score
                    i,                 # 5: indice
                    lugar,             # 6: lugar
                    fecha_req          # 7: fecha_consulta
                ])

        filtered_results.sort(key=lambda x: x[4], reverse=True)

        print(json.dumps({"success": True, "resultados": filtered_results}))

    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    main()