import io
from flask import Flask, render_template, request, Response
from faster_whisper import WhisperModel
import threading
import queue
import uuid
from datetime import datetime
import json
from services.gemini_analyzer import procesar_evento_con_ia

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



from datetime import datetime

@app.route("/transcribe", methods=["POST"])
def transcribe():
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

    if any(palabra in texto.lower() for palabra in PALABRAS_CLAVE):
        evento_id = str(uuid.uuid4())
        
        # Crear evento básico
        evento = {
            "id": evento_id,
            "texto": texto,  # Guardamos el texto transcrito
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"🤖 Iniciando análisis de IA para: {texto[:50]}...")
        
        # Procesar con IA de forma síncrona para obtener el análisis
        try:
            evento_enriquecido = procesar_evento_con_ia(evento)
            print(f"✅ Análisis completado para evento: {evento_id}")
            
            # Guardar evento con análisis
            eventos_detectados.append(evento_enriquecido)
            
        except Exception as e:
            print(f"Error procesando con IA: {e}")
            # Si falla IA, usar evento básico
            eventos_detectados.append(evento)

        # SSE con mensaje simple para el index (no el análisis completo)
        notificacion = {
            "mensaje": "⚠️ Posible amenaza detectada",  # Mensaje simple para index
            "evento_id": evento_id
        }

        event_queue.put(notificacion)

    return {"output": texto}



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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
