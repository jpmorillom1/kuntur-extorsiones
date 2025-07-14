import time
import io
import cv2
import imageio
import b2sdk.v2

def grabar_y_subir_video(camera_ip_url, bucket_name, key_id, app_key):
    cap = cv2.VideoCapture(camera_ip_url)
    if not cap.isOpened():
        raise RuntimeError("No se pudo conectar a la cámara IP.")

    fps = 20
    segundos = 5
    total_frames = fps * segundos

    video_buffer = io.BytesIO()
    writer = imageio.get_writer(video_buffer, format='mp4', fps=fps, macro_block_size=None)

    try:
        frames_grabados = 0
        while frames_grabados < total_frames:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ No se pudo leer frame, reintentando...")
                time.sleep(0.05)  # pequeña espera si falla
                continue
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frames_grabados += 1
    finally:
        cap.release()
        writer.close()

    # Subir a Backblaze
    info = b2sdk.v2.InMemoryAccountInfo()
    b2_api = b2sdk.v2.B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    file_name = f"evidencia_{int(time.time())}.mp4"
    bucket.upload_bytes(video_buffer.getvalue(), file_name)

    return f"https://f005.backblazeb2.com/file/{bucket_name}/{file_name}"
