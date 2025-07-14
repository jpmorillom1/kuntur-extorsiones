document.addEventListener("DOMContentLoaded", function () {
    const map = L.map('map').setView([-0.2299, -78.5249], 13); // Quito como centro

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
    }).addTo(map);

    let marker;

    map.on('click', function (e) {
        const { lat, lng } = e.latlng;
        document.getElementById('lat').value = lat.toFixed(6);
        document.getElementById('lng').value = lng.toFixed(6);

        if (marker) {
            marker.setLatLng([lat, lng]);
        } else {
            marker = L.marker([lat, lng]).addTo(map);
        }

        // Obtener dirección con Nominatim
        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
            .then(response => response.json())
            .then(data => {
                const direccion = data.display_name || "Dirección no encontrada";
                document.querySelector('input[name="ubicacion"]').value = direccion;
            })
            .catch(err => {
                console.error("Error obteniendo dirección:", err);
                document.querySelector('input[name="ubicacion"]').value = "Error obteniendo dirección";
            });
    });
});
