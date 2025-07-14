<p align="center">
  <img src="https://i.ibb.co/V0kz681r/output-onlinepngtools-com.png" alt="Kuntur Logo" width="200"/>
</p>

# 🦅 Kuntur - Sistema AntiExtorsiones

Sistema inteligente para la **detección automática y manual de amenazas** en locales comerciales mediante transcripción de audio, análisis con inteligencia artificial, grabación de evidencia en video y notificación directa a las autoridades (UPC).

---

## 🚨 Funcionalidades principales

- 🎙️ Transcripción en tiempo real con `Faster-Whisper`
- 🧠 Análisis semántico con IA (`Gemini 2.5` + `LangChain`)
- 🔍 Detección de amenazas mediante modelos de lenguaje
- 🎥 Grabación automática de video desde cámara IP
- ☁️ Subida segura de evidencia a `Backblaze B2`
- 📍 Geolocalización del local mediante `Leaflet + Nominatim`
- 🔔 Notificación automática a autoridades en formato `JSON`
- 🖥️ Panel web con alertas en tiempo real vía `Server-Sent Events (SSE)`
- 🔐 Registro y login de locales con sesiones seguras

---

## 🧱 Arquitectura del sistema

```
Frontend (HTML + Bootstrap)
│
├── Registro/Login con sesión (Flask)
│
├── Transcripción (Whisper)
│   └── Evaluación de amenaza (Gemini)
│       └── Análisis profesional en 3-4 líneas
│
├── Grabación desde IP Cam (OpenCV + imageio)
│   └── Subida a Backblaze B2
│
├── MongoDB → Persistencia de alertas y usuarios
│
└── Notificación JSON → API externa de UPC
```

---

## 📦 Instalación y ejecución

### 🔧 Requisitos previos

- Python 3.10+
- MongoDB corriendo local o remoto
- Cámara IP activa (ej. desde app móvil IP Webcam)
- Cuenta en [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html)
- API keys de Gemini

### 📁 Clona el repositorio

```bash
git clone https://github.com/tu_usuario/kuntur-antiextorsiones.git
cd kuntur-antiextorsiones
```

### 📦 Instala dependencias

```bash
pip install -r requirements.txt
```

### 🔑 Configura tu `.env`

```env
SECRET_KEY=una_clave_segura

# Google Gemini API (usa varias claves para rotación)
GOOGLE_API_KEY1=AIzaSy...
GOOGLE_API_KEY2=...
GOOGLE_API_KEY3=...
...

# Backblaze
B2_KEY_ID=xxxxx
B2_APP_KEY=xxxxx

# MongoDB
MONGO_URI=mongodb://localhost:27017/kuntur
```

### 🚀 Ejecuta la aplicación

```bash
python app.py
```

Accede en: [http://localhost:5000](http://localhost:5000)

---

## 📤 Esquema de denuncia (JSON)

```json
{
  "descripcion": "Una persona exige dinero a cambio de no dañar a un familiar. Nivel: CRÍTICO. Recomendación: contactar autoridades.",
  "ubicacion": "Av. Mariscal Sucre y Belisario, Quito",
  "ip_camara": "http://192.168.100.53:8080/video",
  "url": "https://f000.backblazeb2.com/file/kuntur-extorsiones/evidencia_1720983872.mp4"
}
```

---

## ⚙️ Estructura del proyecto

```
📦 stt/
├── app.py                    # App Flask principal
├── .env                      # Variables de entorno
├── routes/
│   ├── auth_routes.py        # Registro y login
│   ├── transcribe_routes.py  # Transcripción y detección
│   ├── alerta_routes.py      # Alerta manual
│   └── stream_routes.py      # Video en vivo (IP Cam)
├── services/
│   ├── gemini_provider.py
│   ├── gemini_analyzer.py    # Análisis con IA
│   ├── threat_detector.py    # Clasificador SI/NO
│   ├── video_uploader.py     # Grabación + subida a Backblaze
│   ├── notificador_upc.py    # Envío de JSON al API UPC
│   ├── global_state.py       # Eventos recientes y SSE
│   ├──auth.py
│   └── db.py                 # Conexión MongoDB
├── templates/                # HTMLs (login, panel)
└── static/                   # CSS, logo, scripts
```

---

## 📚 Tecnologías utilizadas

| Componente      | Herramienta                  |
|----------------|------------------------------|
| Web Framework   | Flask                        |
| Speech-to-Text  | Faster-Whisper               |
| LLM             | Gemini Pro + LangChain       |
| Frontend        | Bootstrap + Leaflet.js       |
| DB              | MongoDB                      |
| Video           | OpenCV + imageio             |
| Cloud Storage   | Backblaze B2                 |
| Notificación    | Server-Sent Events + JSON    |

---
## 🤝 Créditos

Proyecto desarrollado por estudiantes de Ingeniería en Sistemas para la materia de Desarrollo de Sistemas de Información.

- Emily Guerron
- Juan Pablo Morillo  
- Alex Tituaña  


---

