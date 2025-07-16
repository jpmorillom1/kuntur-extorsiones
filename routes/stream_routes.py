# routes/stream_routes.py

import json
import cv2
import queue
from flask import Blueprint, Response, render_template, session
from services.global_state import event_queue, eventos_detectados
from services.db import coleccion_alertas
from bson.json_util import dumps
import time 
from flask import Blueprint, session, Response
from bson.json_util import dumps
from bson import ObjectId
from services.db import coleccion_alertas
import time
from datetime import datetime

stream_bp = Blueprint("stream", __name__)


@stream_bp.route("/stream")
def stream():
    if "usuario_id" not in session:
        return {"error": "No autorizado"}, 403

    usuario_id = ObjectId(session["usuario_id"])

    def event_stream():
        last_timestamp = datetime.now()  # ⚠️ comienza desde "ahora"
        while True:
            # Solo buscar alertas NUEVAS desde el login
            nuevos = list(coleccion_alertas.find({
                "id_usuario": usuario_id,
                "fecha": {"$gt": last_timestamp}
            }).sort("fecha", 1).limit(10))

            for alerta in nuevos:
                last_timestamp = alerta["fecha"]  # avanzar el puntero de tiempo
                yield f"data: {dumps(alerta)}\n\n"

            time.sleep(2)

    return Response(event_stream(), mimetype="text/event-stream")

@stream_bp.route("/alerta/<evento_id>")
def ver_alerta(evento_id):
    evento = next((e for e in eventos_detectados if e["id"] == evento_id), None)
    if not evento:
        return "Evento no encontrado", 404

    return render_template(
        "alerta.html",
        evento=evento,
        ip_camera=evento.get("ip_camara"),
        nombre_local=evento.get("nombre_local"),
        ubicacion=evento.get("ubicacion"),
        latitud=evento.get("latitud"),
        longitud=evento.get("longitud")
    )


@stream_bp.route("/video_feed")
def video_feed():
    if "ip_camara" not in session:
        return "No autorizado", 403

    return Response(
        generar_frames(session["ip_camara"]),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@stream_bp.route("/estado_camara")
def estado_camara():
    ip = session.get("ip_camara")
    if not ip:
        return {"estado": "no disponible"}
    try:
        cap = cv2.VideoCapture(ip)
        success, _ = cap.read()
        cap.release()
        return {"estado": "activa" if success else "inactiva"}
    except:
        return {"estado": "inactiva"}


# Utilidad local
def generar_frames(ip_camara):
    cap = cv2.VideoCapture(ip_camara)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

