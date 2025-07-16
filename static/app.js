const output = document.querySelector(".output");

if (navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        const mediaRecorder = new MediaRecorder(stream);
        let chunks = [];

        mediaRecorder.ondataavailable = function (e) {
            chunks.push(e.data);
        };

        mediaRecorder.onstop = function () {
            const blob = new Blob(chunks, { type: "audio/webm" });
            chunks = [];

            const formData = new FormData();
            formData.append("audio", blob);

            fetch("/transcribe", {
                method: "POST",
                body: formData
            })
            .then((response) => response.json())
            .then((data) => {
                output.innerHTML += `<p>${data.output}</p>`;
            });
        };

        // Función para grabar 5 segundos automáticamente
        function recordFor5Seconds() {
            if (mediaRecorder.state === "inactive") {
                mediaRecorder.start();

                setTimeout(() => {
                    mediaRecorder.stop();
                }, 5000); // 5 segundos
            }
        }
   

        // Repetir grabación cada 5 segundos
        setInterval(recordFor5Seconds, 5000);

    }).catch(function (err) {
        alert("Error al acceder al micrófono: " + err);
    });
} else {
    alert("getUserMedia no es compatible con tu navegador.");
}
