const source = new EventSource("/stream");
const alertContainer = document.getElementById("alert-container");

source.onmessage = function(event) {
  if (event.data.trim() === "") return;
  const data = JSON.parse(event.data);

  const alertDiv = document.createElement("div");
  alertDiv.className = "alert alert-danger alert-dismissible fade show mt-2 recent-alerts";
  alertDiv.setAttribute("role", "alert");
  alertDiv.innerHTML = `
    <i class="bi bi-exclamation-triangle-fill me-1"></i>
    <strong>${data.mensaje}</strong><br>
    <small class="text-muted">${new Date().toLocaleTimeString()}</small><br>
    <a href="/alerta/${data.evento_id}" target="_blank" class="btn btn-sm btn-outline-light mt-1">Ver Detalles</a>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
  `;
  alertContainer.appendChild(alertDiv);
};

source.onerror = function(event) {
  console.log("Error en EventSource:", event);
};
