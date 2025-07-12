from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

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
        prompt = prompt_template.format_messages(texto=texto)
        response = llm.invoke(prompt)
        respuesta = response.content.strip().lower()
        return respuesta == "si"
    except Exception as e:
        print(f"❌ Error en verificación de amenaza: {e}")
        return False
