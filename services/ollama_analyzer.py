from datetime import datetime
from services.ollama_provider import get_llm
from langchain.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    ("human", """
    Eres un analista de seguridad especializado en evaluar amenazas captadas por audio y video.

    CONTEXTO:
    - Se detectó una posible amenaza en una transcripción de audio.
    - Hora de detección: {hora}
    - Transcripción del audio: "{texto_original}"
    - Descripción visual de la escena (generada automáticamente a partir del video grabado): "{descripcion_visual}"

    TAREA:
    Analiza toda la información combinada (audio y descripción visual) y genera UN SOLO PÁRRAFO que incluya:
    - Una interpretación realista de la situación basada en lo escuchado y lo visto (si aplica)
    - Nivel de riesgo estimado (BAJO / MEDIO / ALTO / CRÍTICO)
    - Una recomendación profesional para las autoridades o el personal del local
    - Cita final del texto original entre comillas

    Si la descripción visual aporta información relevante sobre personas, objetos, contexto o acciones visibles, inclúyela brevemente en tu análisis.

    Responde con un texto conciso, profesional y de máximo 4 líneas.
    """)
])

def procesar_evento_con_ia(evento):
    try:
        llm = get_llm()
        prompt = prompt_template.format_messages(
            hora=evento.get('hora'),
            texto_original=evento.get('texto'),
            descripcion_visual=evento.get('descripcion_visual', 'No disponible')
        )
        response = llm.invoke(prompt)
        # response es string, no objeto con .content
        evento.update({
            'analisis_ia': response,
            'timestamp_analisis': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return evento
    except Exception as e:
        print(f"❌ Error específico en Ollama: {type(e).__name__}: {e}")
        evento.update({
            'analisis_ia': f"❌ Error: {str(e)}",
            'timestamp_analisis': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return evento
