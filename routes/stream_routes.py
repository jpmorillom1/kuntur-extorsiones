# routes/stream_routes.py

import json
import cv2
import queue
from flask import Blueprint, Response, render_template, session
from services.global_state import event_queue, eventos_detectados


stream_bp = Blueprint("stream", __name__)


@stream_bp.route("/stream")
def stream():
    def event_stream():
        while True:
            try:
                data = event_queue.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield "data: \n\n"
    return Response(event_stream(), content_type="text/event-stream")


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

