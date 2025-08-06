document.addEventListener('DOMContentLoaded', () => {
    const btnIniciar = document.getElementById('btn-iniciar');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const introMessage = document.getElementById('intro-message');
    const inputUploadFile = document.getElementById('input-upload-file');
    const btnCapturarFoto = document.getElementById('btn-capturar-foto');
    const btnDetectar = document.getElementById('btn-detectar');
    const btnTriangular = document.getElementById('btn-triangular');

    let videoStream = null;

    // Lógica para mostrar/ocultar el sidebar
    btnIniciar.addEventListener('click', () => {
        sidebar.classList.toggle('show');
        mainContent.classList.toggle('pushed');
        if (sidebar.classList.contains('show')) {
            btnIniciar.textContent = 'Salir';
            if (introMessage) introMessage.style.display = 'none';
        } else {
            btnIniciar.textContent = 'Iniciar';
            if (introMessage) introMessage.style.display = 'block';
            
            // Detener la cámara web si está activa
            stopWebcam();
        }
    });

    // Lógica para subir una imagen desde un archivo
    inputUploadFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });

    // Lógica para usar la cámara web
    btnCapturarFoto.addEventListener('click', async () => {
        stopWebcam(); // Detener cualquier stream previo
        try {
            mainContent.innerHTML = `
                <div class="result-container">
                    <h2>Transmisión de la Cámara Web</h2>
                    <video id="webcam-feed" autoplay></video>
                    <button id="btn-capture" class="menu-item">Capturar y Procesar</button>
                </div>
            `;
            const videoElement = document.getElementById('webcam-feed');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoStream = stream;
            videoElement.srcObject = stream;

            const captureButton = document.getElementById('btn-capture');
            captureButton.addEventListener('click', () => {
                captureAndProcess(videoElement);
            });

        } catch (error) {
            console.error("Error al acceder a la cámara:", error);
            mainContent.innerHTML = `
                <div class="intro-message">
                    <h1>Error al acceder a la cámara</h1>
                    <p>Asegúrate de haber dado permisos al navegador.</p>
                </div>
            `;
        }
    });

    function captureAndProcess(videoElement) {
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
            const file = new File([blob], 'webcam_capture.png', { type: 'image/png' });
            await uploadImage(file);
        }, 'image/png');
    }

    function stopWebcam() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
    }

    // Función principal para enviar imágenes al backend
    async function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        mainContent.innerHTML = `
            <div class="intro-message">
                <h1>Subiendo imagen...</h1>
                <p>Esto puede tardar unos segundos.</p>
            </div>
        `;

        try {
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al subir la imagen');
            }

            const result = await response.json();
            displayOriginalImage(result.original_image_url);

        } catch (error) {
            console.error('Error:', error);
            mainContent.innerHTML = `
                <div class="intro-message">
                    <h1>Error</h1>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
    
    // Nueva función para manejar el procesamiento desde los botones
    async function processImage(endpoint, message) {
        mainContent.innerHTML = `
            <div class="intro-message">
                <h1>${message}</h1>
                <p>Esto puede tardar unos segundos.</p>
            </div>
        `;
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
            });
            const result = await response.json();
            if (response.ok) {
                displayProcessedImage(result.image_url, result.message);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            mainContent.innerHTML = `
                <div class="intro-message">
                    <h1>Error</h1>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    // Event listener para el botón de "Detectar Puntos"
    btnDetectar.addEventListener('click', () => {
        processImage('/detect_points', 'Detectando puntos faciales...');
    });
    
    // Event listener para el botón de "Triangular Delaunay"
    btnTriangular.addEventListener('click', () => {
        processImage('/triangulate_delaunay', 'Aplicando triangulación de Delaunay...');
    });

    // Función para mostrar la imagen original al subir
    function displayOriginalImage(imageURL) {
        mainContent.innerHTML = '';
        const gridContainer = document.createElement('div');
        gridContainer.className = 'grid-container';
        gridContainer.innerHTML = `
            <div class="result-container">
                <h2>Imagen Original</h2>
                <img src="${imageURL}" alt="Imagen Original">
            </div>
        `;
        mainContent.appendChild(gridContainer);
    }
    
    // Función para mostrar el resultado procesado
    function displayProcessedImage(imageURL, title) {
        const gridContainer = mainContent.querySelector('.grid-container');
        if (!gridContainer) {
            displayOriginalImage(imageURL);
            return;
        }
        gridContainer.innerHTML += `
            <div class="result-container">
                <h2>${title}</h2>
                <img src="${imageURL}" alt="${title}">
            </div>
        `;
    }
});