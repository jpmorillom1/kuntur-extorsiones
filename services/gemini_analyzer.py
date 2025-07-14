from datetime import datetime
from services.gemini_provider import get_llm
from langchain.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    ("human", """
    Eres un analista de seguridad especializado en evaluar amenazas de audio.
    
    CONTEXTO:
    - Se detectó una posible amenaza en una transcripción de audio
    - Hora de detección: {hora}
    - Texto transcrito: "{texto_original}"
    
    TAREA:
    Analiza el texto y genera UN SOLO PÁRRAFO que incluya:
    - Resumen de la amenaza detectada.
    - Nivel de riesgo (BAJO/MEDIO/ALTO/CRÍTICO).
    - Recomendación básica de acción.
    - Texto original al final entre comillas.

    Máximo 4 líneas, tono profesional.
    """)
])

def procesar_evento_con_ia(evento):
    try:
        llm = get_llm()
        prompt = prompt_template.format_messages(
            hora=evento['hora'],
            texto_original=evento['texto']
        )
        response = llm.invoke(prompt)
        evento.update({
            'analisis_ia': response.content,
            'timestamp_analisis': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return evento
    except Exception as e:
        print(f"❌ Error específico en Gemini: {type(e).__name__}: {e}")
        evento.update({
            'analisis_ia': f"❌ Error: {str(e)}",
            'timestamp_analisis': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return evento
