import os
import random
from itertools import cycle
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Cargar todas las API keys desde la variable
API_KEYS = os.getenv("GOOGLE_API_KEYS", "").split(",")
api_cycle = cycle(API_KEYS)  # Rotación circular

def get_llm():
    """
    Devuelve una instancia de ChatGoogleGenerativeAI con la siguiente API key disponible
    """
    key = next(api_cycle)
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
        convert_system_message_to_human=True,
        google_api_key=key
    )
