# routes/alerta_routes.py

import os
import uuid
from datetime import datetime
from flask import Blueprint, session, request
from bson import ObjectId
from services.gemini_analyzer import procesar_evento_con_ia
from services.video_uploader import grabar_y_subir_video
from services.db import coleccion_alertas
from services.global_state import event_queue, eventos_detectados
from services.notificador_upc import notificar_a_upc
alerta_bp = Blueprint("alerta", __name__)

@alerta_bp.route("/alerta_manual", methods=["POST"])
def alerta_manual():
    if "usuario_id" not in session:
        return {"error": "No autorizado"}, 403

    evento_id = str(uuid.uuid4())
    texto_simulado = "Se reporta una amenaza directa en el lugar. El usuario ha activado una alerta manualmente."

    evento = {
        "id": evento_id,
        "texto": texto_simulado,
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "manual": True,
        "nombre_local": session.get("nombre_local"),
        "ubicacion": session.get("ubicacion"),
        "ip_camara": session.get("ip_camara"),
        "latitud": session.get("latitud"),
        "longitud": session.get("longitud")
    }

    # 2. Captura video y descripción visual
    try:
        link_video, descripcion_visual = grabar_y_subir_video(
            session["ip_camara"],
            bucket_name="kuntur-extorsiones",
            key_id=os.getenv("B2_KEY_ID"),
            app_key=os.getenv("B2_APP_KEY")
        )
        evento["link_evidencia"] = link_video
        evento["descripcion_visual"] = descripcion_visual
    except Exception as e:
        print(f"⚠️ Error subiendo video o generando descripción visual: {e}")
        evento["link_evidencia"] = "No disponible"
        evento["descripcion_visual"] = "No disponible"

    # 3. Procesar evento con IA
    try:
        evento_enriquecido = procesar_evento_con_ia(evento)
    except Exception as e:
        print(f"❌ Error IA manual: {e}")
        evento_enriquecido = evento
        evento_enriquecido["analisis_ia"] = "No disponible"
    eventos_detectados.append(evento_enriquecido)
   
    event_queue.put({
        "mensaje": "🚨 Alerta manual activada",
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
    })

    print("====================")
    print(evento_enriquecido)
    print("====================")

    riesgo = "MEDIO"
    for nivel in ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]:
        if nivel.lower() in evento_enriquecido["analisis_ia"].lower():
            riesgo = nivel
            break

    coleccion_alertas.insert_one({
        "id_usuario": ObjectId(session["usuario_id"]),
        "mensaje": "🚨 Alerta manual activada",
        "evento_id": evento_id,
        "texto": evento_enriquecido["texto"],                     # <- unifica nombre
        "analisis": evento_enriquecido["analisis_ia"],            # <- unifica nombre
        "hora": evento_enriquecido["hora"],                       # <- agrégalo si no está
        "link_evidencia": evento_enriquecido.get("link_evidencia", "No disponible"),
        "ip_camera": evento_enriquecido.get("ip_camara"),         # <- usa mismo nombre inglés
        "nombre_local": evento_enriquecido.get("nombre_local"),
        "ubicacion": evento_enriquecido.get("ubicacion"),
        "latitud": evento_enriquecido.get("latitud"),
        "longitud": evento_enriquecido.get("longitud"),
        "nivel_riesgo": riesgo,
        "fecha": datetime.now()
    })

    notificar_a_upc(
        descripcion=evento_enriquecido["analisis_ia"],
        ubicacion=evento_enriquecido["ubicacion"],
        ip_camara=evento_enriquecido["ip_camara"],
        url_evidencia=evento_enriquecido.get("link_evidencia")
    )




    return {"status": "ok", "evento_id": evento_id}
