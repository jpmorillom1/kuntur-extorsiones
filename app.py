import os
from dotenv import load_dotenv
from flask import Flask
from faster_whisper import WhisperModel

from routes.auth_routes import auth_bp
from routes.transcribe_routes import transcribe_bp
from routes.stream_routes import stream_bp
from routes.alerta_routes import alerta_bp
from services.global_state import event_queue, eventos_detectados

# Cargar variables de entorno
load_dotenv()

# Inicializar aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mi_clave_secreta")

# Cargar modelo Whisper una vez al inicio
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# Registrar Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transcribe_bp)
app.register_blueprint(stream_bp)
app.register_blueprint(alerta_bp)

# Filtro personalizado para escapar texto en JS
@app.template_filter('escapejs')
def escapejs_filter(value):
    import json
    return json.dumps(str(value))[1:-1] if value else ''

# Ejecutar app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
