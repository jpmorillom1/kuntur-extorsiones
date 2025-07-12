import io
from flask import Flask, render_template, request, Response
from faster_whisper import WhisperModel
import threading
import queue
import uuid
from datetime import datetime
import json
from services.gemini_analyzer import procesar_evento_con_ia
import cv2
from services.video_uploader import grabar_y_subir_video
import os
from dotenv import load_dotenv
from services.threat_detector import es_texto_amenaza


# Nueva variable global para guardar detalles
eventos_detectados = []  # cada elemento será un dict con id, texto y timestamp
# Dirección IP de la cámara (puede venir desde una BD en el futuro)
IP_CAMARA = "http://192.168.100.53:8080/video"  # IP Webcam del celular

app = Flask(__name__)
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# Palabras clave para alerta
PALABRAS_CLAVE = {"extorsión", "arma", "matar", "dinero", "amenaza"}



# Cola de eventos SSE
event_queue = queue.Queue()

@app.route("/")
def index():
    return render_template("index.html",ip_camera=IP_CAMARA)





@app.route("/transcribe", methods=["POST"])
def transcribe():
    file = request.files["audio"]       #Recibe el audio
    buffer = io.BytesIO(file.read())    #Convierte en bytes

    # Guardar el audio temporalmente
    temp_path = "temp_audio.webm"
    with open(temp_path, "wb") as f:
        f.write(buffer.getbuffer())

    # Transcribir el audio
    segments, _ = whisper_model.transcribe(
        temp_path,
        language="es",
        beam_size=5,
        vad_filter=True #Detecta cuando hay voz
    )

    # Une todo el texto transcrito
    texto = " ".join(segment.text for segment in segments)

    # Verificar si hay palabras clave
    if es_texto_amenaza(texto):
        evento_id = str(uuid.uuid4()) # Generar ID único para el evento
        
        # Crear evento básico
        evento = {
            "id": evento_id,
            "texto": texto,
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        print(f"🤖 Iniciando análisis de IA para: {texto[:50]}...")

        # Análisis con IA
        try:
            evento_enriquecido = procesar_evento_con_ia(evento)
        except Exception as e:
            print(f"❌ Error procesando con IA: {e}")
            evento_enriquecido = evento
            evento_enriquecido["analisis_ia"] = "No disponible"
            evento_enriquecido["timestamp_analisis"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Subir evidencia de video
        try:
            print("🎥 Grabando video de evidencia...")
            link_video = grabar_y_subir_video(
                IP_CAMARA,
                bucket_name="kuntur-extorsiones",
                key_id=os.getenv("B2_KEY_ID"),
                app_key=os.getenv("B2_APP_KEY")
            )
            evento_enriquecido["link_evidencia"] = link_video
            print(f"📹 Video subido: {link_video}")
        except Exception as e:
            print(f"⚠️ No se pudo subir el video: {e}")
            evento_enriquecido["link_evidencia"] = "No disponible"

        # Guardar el evento
        eventos_detectados.append(evento_enriquecido)

        # Enviar notificación por SSE
        notificacion = {
            "mensaje": "🚨 Alerta crítica detectada",
            "evento_id": evento_id,
            "texto": evento_enriquecido["texto"],
            "link_evidencia": evento_enriquecido.get("link_evidencia", ""),
            "ip_camera": IP_CAMARA,
            "analisis": evento_enriquecido.get("analisis_ia", "Sin análisis"),
            "hora": evento_enriquecido["hora"]
        }
        print(notificacion)
        event_queue.put(notificacion)


    # Respuesta al cliente
    return {"output": texto}



#Mantiene la conexión abierta para enviar eventos SSE
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
    return render_template("alerta.html", evento=evento, ip_camera=IP_CAMARA)

#Mantiene la camara abierta en vivo
def generar_frames():
    cap = cv2.VideoCapture(IP_CAMARA)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/alerta_manual", methods=["POST"])
def alerta_manual():
    evento_id = str(uuid.uuid4())
    texto_simulado = "Se reporta una amenaza directa en el lugar, se requiere atención inmediata."

    evento = {
        "id": evento_id,
        "texto": texto_simulado,
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "manual": True  # Puedes usar esto para distinguir
    }

    # Procesar con IA
    try:
        evento_enriquecido = procesar_evento_con_ia(evento)
    except Exception as e:
        print(f"❌ Error IA en alerta manual: {e}")
        evento_enriquecido = evento
        evento_enriquecido["analisis_ia"] = "No disponible"
        evento_enriquecido["timestamp_analisis"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Subir evidencia de video
    try:
        print("🎥 Grabando video de evidencia (manual)...")
        link_video = grabar_y_subir_video(
            IP_CAMARA,
            bucket_name="kuntur-extorsiones",
            key_id=os.getenv("B2_KEY_ID"),
            app_key=os.getenv("B2_APP_KEY")
        )
        evento_enriquecido["link_evidencia"] = link_video
        print(f"📹 Video subido: {link_video}")
    except Exception as e:
        print(f"⚠️ No se pudo subir el video: {e}")
        evento_enriquecido["link_evidencia"] = "No disponible"

    eventos_detectados.append(evento_enriquecido)

    notificacion = {
        "mensaje": "🚨 Alerta manual activada",
        "evento_id": evento_id
    }
    event_queue.put(notificacion)

    return {"status": "ok", "evento_id": evento_id}


@app.route("/estado_camara")
def estado_camara():
    try:
        cap = cv2.VideoCapture(IP_CAMARA)
        success, _ = cap.read()
        cap.release()
        if success:
            return {"estado": "activa"}
        else:
            return {"estado": "inactiva"}
    except:
        return {"estado": "inactiva"}





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)