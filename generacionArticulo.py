import sys
import json
import traceback

def procesar_noticias(noticias):
    return noticias

if __name__ == "__main__":
    try:
        # Lee la entrada de stdin
        entrada_json = sys.stdin.read()
        
        # Intenta deserializar la cadena JSON a una estructura de datos de Python
        noticias = json.loads(entrada_json)
        
        # Procesa las noticias (esta función es donde agregarías tu lógica específica)
        noticias_procesadas = procesar_noticias(noticias)
        
        # Serializa el resultado a JSON y lo imprime
        print(json.dumps({"success": True, "data": noticias_procesadas}))
        
    except json.JSONDecodeError as e:
        # Maneja errores específicos de JSON
        print(json.dumps({"success": False, "error": "Error al deserializar el argumento JSON", "details": str(e)}))
    except Exception as e:
        # Maneja cualquier otro error
        error_info = traceback.format_exc()
        print(json.dumps({"success": False, "error": "Error inesperado", "details": str(e), "trace": error_info}))

