# services/ollama_provider.py
from langchain_community.llms import Ollama

def get_llm():
    """
    Devuelve una instancia del modelo local de Ollama.
    Asegúrate de tener Ollama corriendo con el modelo adecuado.
    """
    return Ollama(
        model="llama3",       # Puedes usar mistral, codellama, gemma, etc.
        temperature=0.4,
    )
