# routes/transcribe_routes.py

import io
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, session
from bson import ObjectId
from faster_whisper import WhisperModel
from services.threat_detector import es_texto_amenaza
from services.gemini_analyzer import procesar_evento_con_ia
from services.video_uploader import grabar_y_subir_video
from services.db import coleccion_alertas
from services.notificador_upc import notificar_a_upc

transcribe_bp = Blueprint("transcribe", __name__)
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

@transcribe_bp.route("/transcribe", methods=["POST"])
def transcribe():
    if "usuario_id" not in session:
        return {"error": "No autorizado"}, 403

    file = request.files["audio"]
    buffer = io.BytesIO(file.read())
    temp_path = "temp_audio.webm"

    with open(temp_path, "wb") as f:
        f.write(buffer.getbuffer())

    segments, _ = whisper_model.transcribe(
        temp_path,
        language="es",
        beam_size=5,
        vad_filter=True
    )

    texto = " ".join(segment.text for segment in segments)

    if not es_texto_amenaza(texto):
        return {"output": texto}

    evento_id = str(uuid.uuid4())
    ahora = datetime.now()
    documento_inicial = {
        "id_usuario": ObjectId(session["usuario_id"]),
        "mensaje": "🚨 Alerta crítica detectada",
        "evento_id": evento_id,
        "texto": texto,
        "texto_detectado": texto,
        "hora": ahora.strftime("%Y-%m-%d %H:%M:%S"),
        "fecha": ahora,
        "nombre_local": session.get("nombre_local"),
        "ubicacion": session.get("ubicacion"),
        "ip_camara": session.get("ip_camara"),
        "latitud": session.get("latitud"),
        "longitud": session.get("longitud"),
        "nivel_riesgo": "MEDIO",
        "analisis": "Procesando...",
        "link_evidencia": "Procesando...",
        "descripcion_visual": "Procesando...",
        "parte_policial": "standby",  
        "sentencia": "standby"  
    }

    coleccion_alertas.insert_one(documento_inicial)

    # Ahora obtener ID de Mongo
    doc_mongo = coleccion_alertas.find_one({"evento_id": evento_id})

    # Capturar video y descripción visual
    try:
        link_video, descripcion_visual = grabar_y_subir_video(
            session["ip_camara"],
            bucket_name="kuntur-extorsiones",
            key_id=os.getenv("B2_KEY_ID"),
            app_key=os.getenv("B2_APP_KEY")
        )
    except Exception as e:
        print(f"⚠️ Error subiendo video o generando descripción visual: {e}")
        link_video = "No disponible"
        descripcion_visual = "No disponible"

    # Analizar con IA
    try:
        evento = {
            "id": evento_id,
            "texto": texto,
            "hora": documento_inicial["hora"],
            "nombre_local": documento_inicial["nombre_local"],
            "ubicacion": documento_inicial["ubicacion"],
            "ip_camara": documento_inicial["ip_camara"],
            "latitud": documento_inicial["latitud"],
            "longitud": documento_inicial["longitud"],
            "descripcion_visual": descripcion_visual,
            "link_evidencia": link_video
        }
        analisis = procesar_evento_con_ia(evento)
        descripcion_ia = analisis["analisis_ia"]
    except Exception as e:
        print(f"❌ Error IA: {e}")
        descripcion_ia = "No disponible"

    # Nivel de riesgo
    riesgo = "MEDIO"
    for nivel in ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]:
        if nivel.lower() in descripcion_ia.lower():
            riesgo = nivel
            break

    # Actualizar documento
    coleccion_alertas.update_one(
        {"_id": doc_mongo["_id"]},
        {"$set": {
            "analisis": descripcion_ia,
            "link_evidencia": link_video,
            "descripcion_visual": descripcion_visual,
            "nivel_riesgo": riesgo
        }}
    )

    

    # Notificar UPC
    notificar_a_upc(
        descripcion=descripcion_ia,
        ubicacion=documento_inicial["ubicacion"],
        ip_camara=documento_inicial["ip_camara"],
        url_evidencia=link_video,
        id_usuario=session["usuario_id"],
        id_alerta= evento_id        
    )

    return {"output": texto}
