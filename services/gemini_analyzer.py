import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

# Cargar variables de entorno
load_dotenv()

# Obtener API key
api_key = os.getenv("GOOGLE_API_KEY")

# Inicializar modelo Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.4,
    convert_system_message_to_human=True,
    google_api_key=api_key
)

# Template para el prompt
prompt_template = ChatPromptTemplate.from_messages([
    ("human", """
    Eres un analista de seguridad especializado en evaluar amenazas de audio.
    
    CONTEXTO:
    - Se detectó una posible amenaza en una transcripción de audio
    - Hora de detección: {hora}
    - Texto transcrito: "{texto_original}"
    
    TAREA:
    Analiza el texto y genera UN SOLO PÁRRAFO que incluya:
    - Resumen de la amenaza detectada, pero simula una extorsión o amenaza realista y describela de manera breve: Por ejemplo, "Una persona está exigiendo dinero a cambio de no hacer daño a alguien".
    - Nivel de riesgo (BAJO/MEDIO/ALTO/CRÍTICO)  
    - Recomendación básica de acción
    - cada una de estas partes debe estar separada por un punto y aparte.
    - Coloca el texto original al final del análisis, entre comillas. Ejemplo: "Texto original aquí: y ahi el texto original entre comillas".
    
    Responde en un párrafo de máximo 3-4 líneas, mantén un tono profesional.
    """)
])

def procesar_evento_con_ia(evento):
    """
    Procesa un evento con IA y retorna el análisis
    """
    try:
        print(f"📝 Creando prompt para: {evento['texto'][:30]}...")
        
        # Crear prompt
        prompt = prompt_template.format_messages(
            hora=evento['hora'],
            texto_original=evento['texto']
        )
        
        print(f"🔄 Enviando a Gemini...")
        # Obtener análisis
        response = llm.invoke(prompt)
        
        print(f"✅ Respuesta recibida: {len(response.content)} caracteres")
        print(f"📄 Contenido: {response.content[:100]}...")
        
        # Actualizar evento
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
