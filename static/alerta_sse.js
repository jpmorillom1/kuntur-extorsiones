document.addEventListener("DOMContentLoaded", () => {
  const pathSegments = window.location.pathname.split("/");
  const eventoId = pathSegments[pathSegments.length - 1];

  const source = new EventSource(`/stream_alerta/${eventoId}`);

  source.onmessage = function (event) {
    const alerta = JSON.parse(event.data);

    // 🔁 Actualizar análisis IA si está disponible
    const analisisElem = document.getElementById("analisis-ia");
    if (alerta.analisis && analisisElem && analisisElem.innerText !== alerta.analisis) {
      analisisElem.innerText = alerta.analisis;
    }

    // 🔁 Actualizar enlace al video si se ha subido y no está ya en el DOM
    if (alerta.link_evidencia && alerta.link_evidencia !== "No disponible") {
      let btn = document.getElementById("btn-evidencia");

      if (!btn) {
        const div = document.createElement("div");
        div.className = "mb-3";

        btn = document.createElement("a");
        btn.id = "btn-evidencia";
        btn.className = "btn btn-outline-primary";
        btn.target = "_blank";
        btn.innerText = "🎥 Ver evidencia grabada";
        btn.href = alerta.link_evidencia;

        div.appendChild(btn);
        const analisisBox = document.getElementById("analisis-ia");
        analisisBox.parentNode.insertBefore(div, analisisBox.nextSibling);
      } else {
        btn.href = alerta.link_evidencia;
      }
    }
  };
});
