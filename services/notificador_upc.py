import requests

def notificar_a_upc(descripcion, ubicacion, ip_camara, url_evidencia=None):
    payload = {
        "descripcion": descripcion,
        "ubicacion": ubicacion,
        "ip_camara": ip_camara
    }
    if url_evidencia:
        payload["url"] = url_evidencia


    try:
        respuesta = requests.post(
            "http://localhost:8000/api/denuncias",
            json=payload,
            timeout=10
        )


        print("===================")
        print(payload)
        print("===================")
        print(f"✅ Notificación enviada a UPC. Código: {respuesta.status_code}")
        return respuesta.status_code == 200
        
    
    except Exception as e:
        print(f"❌ Error notificando a UPC: {e}")
        return False
