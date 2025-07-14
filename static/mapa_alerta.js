document.addEventListener('DOMContentLoaded', function () {
  const lat = parseFloat(document.getElementById('mapa-ubicacion').dataset.lat);
  const lng = parseFloat(document.getElementById('mapa-ubicacion').dataset.lng);
  const nombreLocal = document.getElementById('mapa-ubicacion').dataset.nombre;
  const direccion = document.getElementById('mapa-ubicacion').dataset.direccion;

  if (!isNaN(lat) && !isNaN(lng)) {
    const map = L.map('mapa-ubicacion').setView([lat, lng], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    L.marker([lat, lng]).addTo(map)
      .bindPopup(`<b>${nombreLocal}</b><br>${direccion}`)
      .openPopup();
  } else {
    document.getElementById('mapa-ubicacion').innerHTML =
      '<div class="alert alert-warning text-center p-4">No hay coordenadas disponibles para mostrar el mapa</div>';
  }
});
