import google.generativeai as genai
GOOGLE_API_KEY= "AIzaSyBieAAYXWNfR5hnBj8D0BnTJKhAEkmQpmM"

genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
    "temperature": 0.5,
    "max_output_tokens": 500,
}

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

model = genai.GenerativeModel(model_name="gemini-pro",
                              safety_settings=safety_settings)

texto_noticias = "Justo 56 años después de que el plantón y ocupación estudiantil contra la guerra de Vietnam en la Universidad de Columbia fue reprimido con violencia por la policía en 1968, el martes por la noche cientos de policías antimotines asaltaron el mismo edificio académico en el campus de esa prestigiosa casa de estudios, arrestando a más de 100 estudiantes."
fecha = "1 de mayo del 2024"
lugar = "Nueva York"
context = "Tu tarea es escribir artículos de noticia que contengan siempre una fecha, un lugar y un acontecimiento. No puedes inventar información que no se te da, utiliza lenguaje formal."
prompt = f"{context} Crea un artículo de noticias con esta información: {texto_noticias}. Fecha: {fecha}. Lugar: {lugar}."
response = model.generate_content(prompt)

if not response.parts:
    print("Content blocked. Safety ratings:", response.safety_ratings)
else:
    print(response.text)
