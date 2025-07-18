from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import requests

app = FastAPI()

# Modelo que Kuntur enviará a UPC
class DenunciaExternaIn(BaseModel):
    descripcion: str
    ubicacion: str
    ip_camara: Optional[str] = None
    url: Optional[str] = None
    id_usuario: Optional[str] = None
    id_alerta: Optional[str] = None

# Endpoint 1: UPC recibe la denuncia
@app.post("/api/denuncias")
def recibir_denuncia(data: DenunciaExternaIn):
    print("📩 Denuncia recibida en UPC:")
    print(data)

    # Simular respuesta de justicIA
    payload = {
        "evento_id": data.id_alerta,
        "id_usuario": data.id_usuario,
        "parte_policial": "Informe policial generado automáticamente por justicIA.",
        "sentencia": "Sentencia preliminar asignada por justicIA."
    }

    try:
        response = requests.post("http://localhost:5000/actualizar_alerta_externa", json=payload)
        print("📨 Enviado a Kuntur desde justicIA. Código:", response.status_code)
        print(response.json())
    except Exception as e:
        print("❌ Error al enviar a Kuntur:", e)

    return {"mensaje": "Denuncia procesada por UPC y reenviada a justicIA"}
