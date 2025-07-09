import cv2
import time
import io
import b2sdk.v2
import imageio
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/grabar_y_subir', methods=['GET'])
def grabar_y_subir():
    # Dirección de la cámara IP
    camera_ip_url = "http://192.168.100.53:8080/video"
    
    # Configuración de la conexión con la cámara
    cap = cv2.VideoCapture(camera_ip_url)

    if not cap.isOpened():
        return jsonify({"error": "No se pudo conectar a la cámara."}), 400

    # Configuración de la API de Backblaze
    application_key_id = ''
    application_key = ''
    bucket_name = 'kuntur-extorsiones'

    # Inicialización de la cuenta de Backblaze
    info = b2sdk.v2.InMemoryAccountInfo()
    b2_api = b2sdk.v2.B2Api(info)
    b2_api.authorize_account('production', application_key_id, application_key)

    # Obtener el bucket por nombre
    bucket = b2_api.get_bucket_by_name(bucket_name)

    # Grabar el video durante 10 segundos y guardar en memoria
    start_time = time.time()
    duration = 10  # Duración en segundos para la grabación
    
    # Crear un buffer en memoria para almacenar el video
    video_buffer = io.BytesIO()
    
    # Usar imageio para escribir el video en memoria
    writer = imageio.get_writer(video_buffer, format='mp4', fps=20, macro_block_size=None)

    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()

        if ret:
            # Escribir el fotograma en el buffer de video
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        else:
            break

    cap.release()
    writer.close()

    # Convertir el buffer en memoria a un formato adecuado para subirlo
    video_data = video_buffer.getvalue()

    # Subir el archivo de video a Backblaze
    file_name = f"video_{int(time.time())}.mp4"
    bucket.upload_bytes(video_data, file_name)

    return jsonify({"message": "Video grabado y subido correctamente."})

if __name__ == '__main__':
    app.run(debug=True)
