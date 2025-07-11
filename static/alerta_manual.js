document.getElementById("activarAlertaManual").addEventListener("click", function() {
  fetch("/alerta_manual", { method: "POST" })
    .then(res => res.json())
    .then(data => {
      console.log("Alerta manual activada:", data);
    })
    .catch(err => {
      console.error("Error activando alerta manual:", err);
    });
});
