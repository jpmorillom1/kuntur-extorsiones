import requests

def notificar_a_upc(descripcion, ubicacion, ip_camara=None, url_evidencia=None):
    url = "https://upc-kuntur.onrender.com/denuncia"

    data = {
        "descripcion": descripcion,
        "ubicacion": ubicacion,
    }

    if url_evidencia:
        data["url"] = url_evidencia

    if ip_camara:
        data["url_stream"] = ip_camara

    try:
        response = requests.post(url, data=data, timeout=10)
        print("===================")
        print("Payload:", data)
        print("Código de respuesta:", response.status_code)
        print("Respuesta:", response.text)
        print("===================")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error notificando a UPC: {e}")
        return False
