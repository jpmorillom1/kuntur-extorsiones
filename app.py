import io
from flask import Flask, render_template, request
from faster_whisper import WhisperModel

# Cargar el modelo una vez al iniciar la aplicación
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/transcribe", methods=["POST"])
    def transcribe():
        file = request.files["audio"]
        buffer = io.BytesIO(file.read())
        
        # Guardar el audio en un archivo temporal (Faster Whisper trabaja con archivos)
        temp_path = "temp_audio.webm"
        with open(temp_path, "wb") as f:
            f.write(buffer.getbuffer())
        
        # Realizar la transcripción
        segments, info = whisper_model.transcribe(
            temp_path,
            language="es",
            beam_size=5,
            vad_filter=True
        )
        
        # Unir todos los segmentos de texto
        transcript_text = " ".join(segment.text for segment in segments)
        
        return {"output": transcript_text}

    return app