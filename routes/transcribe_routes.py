# routes/transcribe_routes.py

import io
import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, session, Response, render_template
from bson import ObjectId
from faster_whisper import WhisperModel

from services.threat_detector import es_texto_amenaza
from services.gemini_analyzer import procesar_evento_con_ia
from services.video_uploader import grabar_y_subir_video
from services.db import coleccion_alertas
from services.global_state import  event_queue, eventos_detectados
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

    if es_texto_amenaza(texto):
        evento_id = str(uuid.uuid4())
        evento = {
            "id": evento_id,
            "texto": texto,
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre_local": session.get("nombre_local"),
            "ubicacion": session.get("ubicacion"),
            "ip_camara": session.get("ip_camara"),
            "latitud": session.get("latitud"),
            "longitud": session.get("longitud")
        }

        try:
            evento_enriquecido = procesar_evento_con_ia(evento)
        except Exception as e:
            print(f"❌ Error IA: {e}")
            evento_enriquecido = evento
            evento_enriquecido["analisis_ia"] = "No disponible"

        try:
            link_video = grabar_y_subir_video(
                session["ip_camara"],
                bucket_name="kuntur-extorsiones",
                key_id=os.getenv("B2_KEY_ID"),
                app_key=os.getenv("B2_APP_KEY")
            )
            evento_enriquecido["link_evidencia"] = link_video
        except Exception as e:
            print(f"⚠️ Error subiendo video: {e}")
            evento_enriquecido["link_evidencia"] = "No disponible"

        eventos_detectados.append(evento_enriquecido)

        notificacion = {
            "mensaje": "🚨 Alerta crítica detectada",
            "evento_id": evento_id,
            "texto": evento_enriquecido["texto"],
            "link_evidencia": evento_enriquecido.get("link_evidencia", ""),
            "ip_camera": evento_enriquecido.get("ip_camara"),
            "analisis": evento_enriquecido.get("analisis_ia", "Sin análisis"),
            "hora": evento_enriquecido["hora"],
            "nombre_local": evento_enriquecido.get("nombre_local"),
            "ubicacion": evento_enriquecido.get("ubicacion"),
            "latitud": evento_enriquecido.get("latitud"),
            "longitud": evento_enriquecido.get("longitud")
        }

        print("🔔 Notificación:", notificacion)
        event_queue.put(notificacion)

        # Guardar en MongoDB
        riesgo = "MEDIO"
        for nivel in ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]:
            if nivel.lower() in evento_enriquecido["analisis_ia"].lower():
                riesgo = nivel
                break

        coleccion_alertas.insert_one({
            "id_usuario": ObjectId(session["usuario_id"]),
            "nombre_local": evento_enriquecido.get("nombre_local"),
            "ubicacion": evento_enriquecido.get("ubicacion"),
            "ip_camara": evento_enriquecido.get("ip_camara"),
            "latitud": evento_enriquecido.get("latitud"),
            "longitud": evento_enriquecido.get("longitud"),
            "texto_detectado": evento_enriquecido["texto"],
            "descripcion_alerta": evento_enriquecido["analisis_ia"],
            "nivel_riesgo": riesgo,
            "fecha": datetime.now(),
            "link_evidencia": evento_enriquecido.get("link_evidencia", "No disponible")
        })

        notificar_a_upc(
            descripcion=evento_enriquecido["analisis_ia"],
            ubicacion=evento_enriquecido["ubicacion"],
            ip_camara=evento_enriquecido["ip_camara"],
            url_evidencia=evento_enriquecido.get("link_evidencia")
        )

    return {"output": texto}
