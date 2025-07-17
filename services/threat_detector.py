from services.gemini_provider import get_llm
from langchain.prompts import ChatPromptTemplate
prompt_template = ChatPromptTemplate.from_messages([
    ("human", """
    Eres un sistema de seguridad que analiza textos transcritos de audio para detectar amenazas o extorsiones.

    A continuación se proporciona una lista de bandas delincuenciales de Ecuador. Considera que cualquier referencia a estas bandas, ya sea mencionando su nombre o indicando pertenencia, apoyo, o relación con ellas, podría representar una amenaza real o una señal de riesgo, incluso si el texto no contiene lenguaje explícito de extorsión, intimidación o coacción.

    Bandas delincuenciales de Ecuador:
    - Águilas
    - Águilas Killer
    - Ak47 
    - Caballeros Oscuros 
    - ChoneKiller
    - Choneros 
    - Corvicheros
    - Cuartel de las Feas
    - Cubanos 
    - Fatales 
    - Gånster 
    - Kater Piler 
    - Lagartos 
    - Latin Kings 
    - Lobos
    - Los p.27
    - Los Tiburones
    - Mafia 18 
    - Mafia Trébol 
    - Patrones 
    - R7 
    - Tiguerones

    Evalúa el siguiente texto y responde solo con "SI" si representa una amenaza real, lo cual incluye:

    - Extorsión, intimidación, coacción u otros actos violentos explícitos.
    - Cualquier referencia o mención directa a alguna de estas bandas, incluyendo pertenencia, apoyo, amenaza o alianza.

    Responde "NO" solamente si el texto es completamente inocuo y no menciona ni implica relación con ninguna de estas bandas ni contiene amenazas.

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
