document.addEventListener('DOMContentLoaded', () => {
    const btnIniciar = document.getElementById('btn-iniciar');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const introMessage = document.getElementById('intro-message');
    const inputUploadFile = document.getElementById('input-upload-file');
    const btnCapturarFoto = document.getElementById('btn-capturar-foto');
    const btnDetectar = document.getElementById('btn-detectar');
    const btnTriangular = document.getElementById('btn-triangular');
    const btnSalvar = document.getElementById('btn-salvar');
    const numPointsInput = document.getElementById('num_points');

    let videoStream = null;
    let currentOriginalImageURL = null;
    let currentDetectedImageURL = null;
    let currentPointsOnlyURL = null;

    btnIniciar.addEventListener('click', () => {
        sidebar.classList.toggle('show');
        mainContent.classList.toggle('pushed');
        if (sidebar.classList.contains('show')) {
            btnIniciar.textContent = 'Salir';
            if (introMessage) introMessage.style.display = 'none';
        } else {
            btnIniciar.textContent = 'Iniciar';
            if (introMessage) mainContent.innerHTML = '';
            if (introMessage) mainContent.appendChild(introMessage);
            introMessage.style.display = 'block';
            stopWebcam();
            currentOriginalImageURL = null;
            currentDetectedImageURL = null;
            currentPointsOnlyURL = null;
        }
    });

    inputUploadFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });

    btnCapturarFoto.addEventListener('click', async () => {
        stopWebcam();
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
            currentOriginalImageURL = result.original_image_url;
            displayInitialResult(result.original_image_url);
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

    async function processImage(endpoint, message) {
        if (!currentOriginalImageURL) {
            return;
        }

        let numPoints = 0;
        if (numPointsInput) {
            numPoints = numPointsInput.value;
        }

        mainContent.innerHTML = `
            <div class="intro-message">
                <h1>${message}</h1>
                <p>Esto puede tardar unos segundos.</p>
            </div>
        `;
        try {
            const fetchURL = endpoint === '/detect_points' ? `${endpoint}/${numPoints}` : endpoint;
            const response = await fetch(fetchURL, {
                method: 'POST',
            });
            const result = await response.json();
            if (response.ok) {
                if (endpoint === '/detect_points') {
                    currentDetectedImageURL = result.detected_image_url;
                    currentPointsOnlyURL = result.points_only_url;
                }
                displayProcessedImages(result, endpoint);
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

    btnDetectar.addEventListener('click', () => {
        processImage('/detect_points', 'Detectando puntos faciales...');
    });

    btnTriangular.addEventListener('click', () => {
        processImage('/triangulate_delaunay', 'Aplicando triangulación de Delaunay...');
    });

    btnSalvar.addEventListener('click', () => {
        window.location.href = '/download_image';
    });

    function displayInitialResult(imageURL) {
        mainContent.innerHTML = `
            <div class="grid-container">
                <div class="result-container">
                    <h2>Imagen Original</h2>
                    <img src="${imageURL}" alt="Imagen Original">
                </div>
            </div>
        `;
    }

    function displayProcessedImages(result, endpoint) {
        mainContent.innerHTML = '';
        const gridContainer = document.createElement('div');
        gridContainer.className = 'grid-container';

        if (currentOriginalImageURL) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Imagen Original</h2>
                    <img src="${currentOriginalImageURL}" alt="Imagen Original">
                </div>
            `;
        }

        if (endpoint === '/detect_points' && result.detected_image_url) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Imagen con Puntos</h2>
                    <img src="${result.detected_image_url}" alt="Imagen con Puntos">
                </div>
            `;
        } else if (endpoint === '/triangulate_delaunay' && currentDetectedImageURL) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Imagen con Puntos</h2>
                    <img src="${currentDetectedImageURL}" alt="Imagen con Puntos">
                </div>
            `;
        }
        
        if (endpoint === '/triangulate_delaunay' && result.triangulated_image_url) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Imagen con Triangulación</h2>
                    <img src="${result.triangulated_image_url}" alt="Imagen con Triangulación">
                </div>
            `;
        }

        if (endpoint === '/detect_points' && result.points_only_url) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Solo Puntos</h2>
                    <img src="${result.points_only_url}" alt="Solo puntos">
                </div>
            `;
        } else if (endpoint === '/triangulate_delaunay' && currentPointsOnlyURL) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Solo Puntos</h2>
                    <img src="${currentPointsOnlyURL}" alt="Solo puntos">
                </div>
            `;
        }

        if (endpoint === '/triangulate_delaunay' && result.triangulation_only_url) {
            gridContainer.innerHTML += `
                <div class="result-container">
                    <h2>Solo Triangulación</h2>
                    <img src="${result.triangulation_only_url}" alt="Solo triangulación">
                </div>
            `;
        }

        mainContent.appendChild(gridContainer);
    }
});