async function verificarMicrofono() {
  const micBadge = document.querySelector("#estado-mic");
  const micGrabando = document.querySelector("#estado-mic-grabando");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micBadge.textContent = "Activo";
    micBadge.className = "badge text-bg-success";
    micGrabando.textContent = "Grabando";
    micGrabando.className = "badge bg-light text-dark border";
    stream.getTracks().forEach(track => track.stop());
  } catch (err) {
    micBadge.textContent = "Inactivo";
    micBadge.className = "badge text-bg-danger";
    micGrabando.textContent = "No disponible";
    micGrabando.className = "badge bg-secondary";
  }
}

async function verificarCamaraIP() {
  const camBadge = document.querySelector("#estado-cam");
  const camGrabando = document.querySelector("#estado-cam-grabando");

  try {
    const res = await fetch("/estado_camara");
    const data = await res.json();

    if (data.estado === "activa") {
      camBadge.textContent = "Activa";
      camBadge.className = "badge text-bg-success";
      camGrabando.textContent = "Disponible";
      camGrabando.className = "badge bg-light text-dark border";
    } else {
      camBadge.textContent = "Inactiva";
      camBadge.className = "badge text-bg-danger";
      camGrabando.textContent = "No disponible";
      camGrabando.className = "badge bg-secondary";
    }
  } catch (err) {
    camBadge.textContent = "Error";
    camBadge.className = "badge bg-danger";
  }
}

verificarMicrofono();
verificarCamaraIP();
