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
from flask import render_template, session
from flask import request, jsonify


alerta_bp = Blueprint("alerta", __name__)



@alerta_bp.route("/alerta_manual", methods=["POST"])
def alerta_manual():
    if "usuario_id" not in session:
        return {"error": "No autorizado"}, 403

    evento_id = str(uuid.uuid4())
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    texto_simulado = "Se reporta una amenaza directa en el lugar. El usuario ha activado una alerta manualmente."

    evento_basico = {
        "id_usuario": ObjectId(session["usuario_id"]),
        "mensaje": "🚨 Alerta manual activada",
        "evento_id": evento_id,
        "texto": texto_simulado,
        "hora": hora_actual,
        "ip_camera": session.get("ip_camara"),
        "ip_camara": session.get("ip_camara"),
        "nombre_local": session.get("nombre_local"),
        "ubicacion": session.get("ubicacion"),
        "latitud": session.get("latitud"),
        "longitud": session.get("longitud"),
        "analisis": "En proceso...",
        "descripcion_visual": "En proceso...",
        "link_evidencia": "Procesando...",
        "nivel_riesgo": "En análisis",
        "fecha": datetime.now(),
        "parte_policial": "standby",  
        "sentencia": "standby"  
        
    }

    resultado = coleccion_alertas.insert_one(evento_basico)
    alerta_id = resultado.inserted_id

    # Enviar SSE inmediatamente
    event_queue.put({
        "mensaje": evento_basico["mensaje"],
        "evento_id": evento_id,
        "texto": texto_simulado,
        "hora": hora_actual,
        "ip_camera": evento_basico["ip_camera"],
        "nombre_local": evento_basico["nombre_local"],
        "ubicacion": evento_basico["ubicacion"],
        "latitud": evento_basico["latitud"],
        "longitud": evento_basico["longitud"]
    })

    # Procesamiento en segundo plano
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

    try:
        evento_enriquecido = procesar_evento_con_ia({
            "id": evento_id,
            "texto": texto_simulado,
            "hora": hora_actual,
            "nombre_local": session.get("nombre_local"),
            "ubicacion": session.get("ubicacion"),
            "ip_camara": session.get("ip_camara"),
            "latitud": session.get("latitud"),
            "longitud": session.get("longitud"),
            "descripcion_visual": descripcion_visual
        })
        analisis_ia = evento_enriquecido.get("analisis_ia", "No disponible")
    except Exception as e:
        print(f"❌ Error IA manual: {e}")
        analisis_ia = "No disponible"

    # Determinar nivel de riesgo
    riesgo = "MEDIO"
    for nivel in ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]:
        if nivel.lower() in analisis_ia.lower():
            riesgo = nivel
            break

    # Actualizar documento en MongoDB
    coleccion_alertas.update_one(
        {"_id": alerta_id},
        {"$set": {
            "analisis": analisis_ia,
            "descripcion_visual": descripcion_visual,
            "link_evidencia": link_video,
            "nivel_riesgo": riesgo
        }}
    )

    # Guardar en memoria
    eventos_detectados.append({
        "id": evento_id,
        "texto": texto_simulado,
        "hora": hora_actual,
        "analisis_ia": analisis_ia,
        "ip_camara": session.get("ip_camara"),
        "nombre_local": session.get("nombre_local"),
        "ubicacion": session.get("ubicacion"),
        "latitud": session.get("latitud"),
        "longitud": session.get("longitud"),
        "link_evidencia": link_video
    })

    # Notificación externa
    notificar_a_upc(
        descripcion=analisis_ia,
        ubicacion=evento_basico["ubicacion"],
        ip_camara=evento_basico["ip_camera"],
        url_evidencia=link_video,

    )

    

    return {"status": "ok", "evento_id": evento_id}




@alerta_bp.route("/mis_alertas")
def mis_alertas():
    if "usuario_id" not in session:
        return {"error": "No autorizado"}, 403

    usuario_id = ObjectId(session["usuario_id"])
    alertas = list(coleccion_alertas.find({"id_usuario": usuario_id}).sort("fecha", -1))


    return render_template("mis_alertas.html", alertas=alertas)



@alerta_bp.route("/actualizar_alerta_externa", methods=["POST"])

def actualizar_alerta_externa():
    data = request.get_json()
    try:
        alerta_id = ObjectId(data["evento_id"])  # 👈 convertir a ObjectId
    except Exception as e:
        return {"error": "ID de alerta inválido"}, 400

    result = coleccion_alertas.update_one(
        {"_id": alerta_id},
        {
            "$set": {
                "parte_policial": data.get("parte_policial"),
                "sentencia": data.get("sentencia")
            }
        }
    )

    if result.matched_count == 0:
        return {"error": "Alerta no encontrada"}, 404

    return {"status": "ok", "mensaje": "Alerta actualizada correctamente"}
