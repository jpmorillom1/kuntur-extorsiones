# services/caption_generator.py

from transformers import pipeline
from PIL import Image
import torch
import io

# Pipeline de HuggingFace BLIP
caption_pipe = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

def generar_descripcion(frame_bgr):
    """Convierte un frame (BGR de OpenCV) a PIL y genera un caption."""
    image_rgb = frame_bgr[..., ::-1]  # Convertir BGR a RGB
    image_pil = Image.fromarray(image_rgb)
    resultado = caption_pipe(image_pil)
    return resultado[0]['generated_text']
