const source = new EventSource("/stream");
const alertContainer = document.getElementById("alert-container");
const fullscreenAlert = document.getElementById("fullscreen-alert");

source.onmessage = function(event) {
  if (event.data.trim() === "") return;
  const data = JSON.parse(event.data);

  // 1️⃣ Mostrar en pantalla completa
  fullscreenAlert.innerHTML = `
    <img src="/static/Kuntur_blanco.png" alt="Logo Kuntur" class="alerta-logo">
    <div><strong>${data.mensaje}</strong></div>
  `;

  fullscreenAlert.classList.remove("d-none");

  // Reproducir sonido
  const audio = new Audio("/static/alerta.mp3");
  audio.play();

  // 2️⃣ Después de 3 segundos, ocultar y mover al feed lateral
  setTimeout(() => {
    fullscreenAlert.classList.add("d-none");

    const alertDiv = document.createElement("div");
    alertDiv.className = "alert alert-custom alert-dismissible fade show mt-2 recent-alerts alert-animada";
    alertDiv.setAttribute("role", "alert");
    alertDiv.innerHTML = `
      <i class="bi bi-exclamation-triangle-fill me-1"></i>
      <strong>${data.mensaje}</strong><br>
      <small class="text-muted">${new Date().toLocaleTimeString()}</small><br>
      <a href="/alerta/${data.evento_id}" target="_blank" class="btn btn-sm btn-outline-dark mt-1">Ver Detalles</a>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
    `;
    alertContainer.prepend(alertDiv);
  }, 3000);
};

source.onerror = function(event) {
  console.log("Error en EventSource:", event);
};
