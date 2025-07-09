import time
import io
import cv2
import imageio
import b2sdk.v2

def grabar_y_subir_video(camera_ip_url, bucket_name, key_id, app_key):
    # Iniciar captura
    cap = cv2.VideoCapture(camera_ip_url)

    if not cap.isOpened():
        raise RuntimeError("No se pudo conectar a la cámara IP.")

    # Duración de la grabación
    duration = 5
    start_time = time.time()

    # Crear buffer de video
    video_buffer = io.BytesIO()
    writer = imageio.get_writer(video_buffer, format='mp4', fps=20, macro_block_size=None)

    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if ret:
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            break

    cap.release()
    writer.close()

    # Inicializar Backblaze
    info = b2sdk.v2.InMemoryAccountInfo()
    b2_api = b2sdk.v2.B2Api(info)
    b2_api.authorize_account('production', key_id, app_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    # Subir video
    video_data = video_buffer.getvalue()
    file_name = f"evidencia_{int(time.time())}.mp4"
    file_info = bucket.upload_bytes(video_data, file_name)

    # Retornar URL pública
    return f"https://f000.backblazeb2.com/file/{bucket_name}/{file_name}"
