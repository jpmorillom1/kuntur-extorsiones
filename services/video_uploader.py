import time
import io
import cv2
import imageio
import b2sdk.v2
from services.caption_generator import generar_descripcion


def grabar_y_subir_video(camera_ip_url, bucket_name, key_id, app_key):
    cap = cv2.VideoCapture(camera_ip_url)
    if not cap.isOpened():
        raise RuntimeError("No se pudo conectar a la cámara IP.")

    fps = 20
    segundos = 5
    total_frames = fps * segundos

    # Capturar frames al 25%, 50% y 75% del video
    idxs_para_describir = [
        total_frames // 4,
        total_frames // 2,
        (3 * total_frames) // 4
    ]
    frames_descriptivos = {}

    video_buffer = io.BytesIO()
    writer = imageio.get_writer(video_buffer, format='mp4', fps=fps, macro_block_size=None)

    descripcion_visual = "No disponible"
    try:
        frames_grabados = 0

        while frames_grabados < total_frames:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # Guardar los frames clave
            if frames_grabados in idxs_para_describir:
                frames_descriptivos[frames_grabados] = frame.copy()

            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frames_grabados += 1

        # Generar descripciones si se capturaron los 3 frames
        captions = []
        for idx in sorted(frames_descriptivos.keys()):
            try:
                descripcion = generar_descripcion(frames_descriptivos[idx])
                captions.append(f"Frame {idx}: {descripcion}")
            except Exception as e:
                print(f"❌ Error generando descripción para frame {idx}: {e}")

        if captions:
            descripcion_visual = " | ".join(captions)

    finally:
        cap.release()
        writer.close()

    # Subir video a Backblaze
    info = b2sdk.v2.InMemoryAccountInfo()
    b2_api = b2sdk.v2.B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    file_name = f"evidencia_{int(time.time())}.mp4"
    bucket.upload_bytes(video_buffer.getvalue(), file_name)

    url_video = f"https://f005.backblazeb2.com/file/{bucket_name}/{file_name}"

    return url_video, descripcion_visual
