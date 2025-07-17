document.addEventListener("DOMContentLoaded", () => {
  const pathSegments = window.location.pathname.split("/");
  const eventoId = pathSegments[pathSegments.length - 1];

  const source = new EventSource(`/stream_alerta/${eventoId}`);

  source.onmessage = function (event) {
    const alerta = JSON.parse(event.data);

    // Actualizar análisis IA si está disponible
    const analisisElem = document.querySelector(".alert.alert-warning");
    if (alerta.analisis && analisisElem) {
      analisisElem.innerText = alerta.analisis;
    }

    // Actualizar enlace al video si se ha subido
    if (alerta.link_evidencia && alerta.link_evidencia !== "No disponible") {
      let btn = document.querySelector(".btn.btn-outline-primary");
      if (!btn) {
        // Crear el botón si no existe
        const div = document.createElement("div");
        div.className = "mb-3";
        btn = document.createElement("a");
        btn.className = "btn btn-outline-primary";
        btn.target = "_blank";
        btn.innerText = "🎥 Ver evidencia grabada";
        div.appendChild(btn);
        const body = document.querySelector(".card-body");
        body.appendChild(div);
      }
      btn.href = alerta.link_evidencia;
    }
  };
});
