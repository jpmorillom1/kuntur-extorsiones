import io
import os
import cv2
import uuid
import json
import queue
import threading
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, Response, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from faster_whisper import WhisperModel
from services.gemini_analyzer import procesar_evento_con_ia
from services.video_uploader import grabar_y_subir_video
from services.threat_detector import es_texto_amenaza
from services.db import coleccion_alertas, coleccion_usuarios



# Cargar variables de entorno
load_dotenv()

# Inicializar Flask y modelo de audio
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mi_clave_secreta")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# Cola de eventos SSE
event_queue = queue.Queue()
eventos_detectados = []

# ──────────────────────────────── AUTENTICACIÓN ────────────────────────────────


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre_local"]
        password = request.form["password"]

        usuario = coleccion_usuarios.find_one({"nombre_local": nombre})
        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = str(usuario["_id"])
            session["ip_camara"] = usuario["ip_camara"]
            session["nombre_local"] = usuario["nombre_local"]
            session['ubicacion'] = usuario["ubicacion"]
            session['latitud'] = usuario["latitud"]
            session['longitud'] = usuario["longitud"]
            return redirect("/panel")
        
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nombre = request.form["nombre_local"]
        ubicacion = request.form["ubicacion"]
        ip_camara = request.form["ip_camara"]
        lat = request.form.get("latitud")
        lng = request.form.get("longitud")

        password = generate_password_hash(request.form["password"])
    

        if coleccion_usuarios.find_one({"nombre_local": nombre}):
            return render_template("registro.html", error="El nombre del local ya existe")

        coleccion_usuarios.insert_one({
            "nombre_local": nombre,
            "ubicacion": ubicacion,
            "ip_camara": ip_camara,
            "latitud": float(lat) if lat else None,
            "longitud": float(lng) if lng else None,
            "password": password
        })

        return redirect("/")

    return render_template("registro.html")


@app.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect("/")

    usuario = coleccion_usuarios.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        return redirect("/")

    return render_template(
        "index.html",
        ip_camera=usuario["ip_camara"],
        nombre_local=usuario["nombre_local"],
        ubicacion=usuario["ubicacion"],

    )


# ──────────────────────────────── TRANSCRIPCIÓN ────────────────────────────────

@app.route("/transcribe", methods=["POST"])
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

    # une segmentos de texto
    texto = " ".join(segment.text for segment in segments)

    if es_texto_amenaza(texto):
        evento_id = str(uuid.uuid4())
        evento = {
            "id": evento_id,
            "texto": texto,
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nombre_local" : session.get("nombre_local"),
            "ubicacion" : session.get("ubicacion"),
            "ip_camara" : session.get("ip_camara"),
            "latitud" : session.get("latitud"),
            "longitud" : session.get("longitud")
        }

        try:
            evento_enriquecido = procesar_evento_con_ia(evento)
        except Exception as e:
            print(f"❌ Error IA: {e}")
            evento_enriquecido = evento
            evento_enriquecido["analisis_ia"] = "No disponible"
            evento_enriquecido["nombre_local"] = session.get("nombre_local")
            evento_enriquecido["ubicacion"] = session.get("ubicacion")
            evento_enriquecido["ip_camara"] = session.get("ip_camara")
            evento_enriquecido["latitud"] = session.get("latitud")
            evento_enriquecido["longitud"] = session.get("longitud")

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

        # Notificación por SSE formato JSON (ESTE JSON ES EL QUE SE ENVÍA AL FRONTEND)
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

        print(notificacion)

        event_queue.put(notificacion)

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


    return {"output": texto}





# ──────────────────────────────── STREAMING ────────────────────────────────


@app.route("/stream")
def stream():
    def event_stream():
        while True:
            try:
                data = event_queue.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield "data: \n\n"
    return Response(event_stream(), content_type="text/event-stream")


@app.route("/alerta/<evento_id>")
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







def generar_frames(ip_camara):
    cap = cv2.VideoCapture(ip_camara)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')




@app.route('/video_feed')
def video_feed():
    if "ip_camara" not in session:
        return "No autorizado", 403
    return Response(generar_frames(session["ip_camara"]), mimetype='multipart/x-mixed-replace; boundary=frame')




@app.route("/estado_camara")
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



# ──────────────────────────────── ALERTA MANUAL ────────────────────────────────

@app.route("/alerta_manual", methods=["POST"])
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

    try:
        evento_enriquecido = procesar_evento_con_ia(evento)
    except Exception as e:
        print(f"❌ Error IA manual: {e}")
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

    # Notificación por SSE
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

    # Persistencia en MongoDB
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

    return {"status": "ok", "evento_id": evento_id}



@app.template_filter('escapejs')
def escapejs_filter(value):
    import json
    return json.dumps(str(value))[1:-1] if value else ''




# ──────────────────────────────── MAIN ────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
