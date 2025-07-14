from services.gemini_provider import get_llm
from langchain.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    ("human", """
    Eres un sistema de seguridad que analiza textos transcritos de audio para detectar amenazas o extorsiones.

    Evalúa el siguiente texto y responde solo con "SI" si representa una amenaza real (como extorsión, intimidación, coacción, etc), o "NO" si es inofensivo.

    Texto:
    "{texto}"
    """)
])

def es_texto_amenaza(texto: str) -> bool:
    try:
        llm = get_llm()
        prompt = prompt_template.format_messages(texto=texto)
        response = llm.invoke(prompt)
        return response.content.strip().lower() == "si"
    except Exception as e:
        print(f"❌ Error en verificación de amenaza: {e}")
        return False
