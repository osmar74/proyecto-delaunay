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
    const btnRotar = document.getElementById('btn-rotar');

    let videoStream = null;
    let currentOriginalImageURL = null;
    let currentDetectedImageURL = null;
    let currentPointsOnlyURL = null;
    let lastDisplayedImageURL = null;
    // Nuevo objeto para mantener el estado de la rotación en los tres ejes
    let currentRotation = {x: 0, y: 0, z: 0};

    // Maneja la visibilidad de la barra lateral al hacer clic en "Iniciar".
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
            lastDisplayedImageURL = null;
            currentRotation = {x: 0, y: 0, z: 0};
        }
    });

    // Maneja la carga de archivos cuando se selecciona una imagen.
    inputUploadFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });

    // Maneja la captura de video desde la webcam.
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

    // Captura un fotograma del video y lo envía para su procesamiento.
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

    // Detiene la transmisión de la webcam.
    function stopWebcam() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
    }

    // Sube la imagen seleccionada o capturada al servidor.
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
            lastDisplayedImageURL = currentOriginalImageURL;
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

    // Envía la imagen al backend para detectar puntos o triangular.
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
                    lastDisplayedImageURL = result.detected_image_url;
                } else if (endpoint === '/triangulate_delaunay') {
                    lastDisplayedImageURL = result.triangulation_only_url;
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

    // Event listener para el botón "Detectar Puntos".
    btnDetectar.addEventListener('click', () => {
        processImage('/detect_points', 'Detectando puntos faciales...');
    });

    // Event listener para el botón "Triangular Delaunay".
    btnTriangular.addEventListener('click', () => {
        processImage('/triangulate_delaunay', 'Aplicando triangulación de Delaunay...');
    });

    // Event listener para el botón "Salvar Imagen".
    btnSalvar.addEventListener('click', () => {
        window.location.href = '/download_image';
    });

    // Event listener para el botón "Rotar Imagen".
    // Muestra el menú para ingresar el ángulo de rotación.
    btnRotar.addEventListener('click', () => {
        if (!lastDisplayedImageURL) {
            mainContent.innerHTML = `
                <div class="intro-message">
                    <h1>Aún no hay una imagen procesada</h1>
                    <p>Primero sube o captura una imagen y triangúlala.</p>
                </div>
            `;
            return;
        }
        showRotateMenu(lastDisplayedImageURL, currentRotation);
    });

    // Muestra la interfaz para rotar la imagen con un campo de entrada.
    function showRotateMenu(imageURL, rotation) {
        mainContent.innerHTML = `
            <div class="grid-container">
                <div class="result-container">
                    <h2>Rotar Imagen</h2>
                    <img src="${imageURL}" alt="Imagen para rotar">
                    <div class="rotate-input-container">
                        <label for="rotation-angle-x">Ángulo X (°):</label>
                        <input type="number" id="rotation-angle-x" value="${rotation.x}" step="5" min="-360" max="360" class="menu-item">
                        <label for="rotation-angle-y">Ángulo Y (°):</label>
                        <input type="number" id="rotation-angle-y" value="${rotation.y}" step="5" min="-360" max="360" class="menu-item">
                        <label for="rotation-angle-z">Ángulo Z (°):</label>
                        <input type="number" id="rotation-angle-z" value="${rotation.z}" step="5" min="-360" max="360" class="menu-item">
                        <button id="btn-submit-rotate" class="menu-item rotate-btn"><i class="fas fa-sync-alt"></i> Rotar</button>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('btn-submit-rotate').addEventListener('click', () => {
            const angleX = document.getElementById('rotation-angle-x').value;
            const angleY = document.getElementById('rotation-angle-y').value;
            const angleZ = document.getElementById('rotation-angle-z').value;
            rotateAndReprocess(angleX, angleY, angleZ);
        });
    }

    // Envía la solicitud al backend para rotar la imagen y la reprocesa.
    async function rotateAndReprocess(angleX, angleY, angleZ) {
        mainContent.innerHTML = `
            <div class="intro-message">
                <h1>Rotando y reprocesando...</h1>
                <p>Esto puede tardar unos segundos.</p>
            </div>
        `;

        try {
            const response = await fetch(`/rotate_and_reprocess_3d/${angleX}/${angleY}/${angleZ}`, {
                method: 'POST',
            });
            const result = await response.json();
            if (response.ok) {
                lastDisplayedImageURL = result.reprocessed_image_url;
                currentRotation = {x: angleX, y: angleY, z: angleZ}; // Actualiza el estado de la rotación
                // Vuelve a mostrar el menú de rotación con la nueva imagen y ángulos
                showRotateMenu(lastDisplayedImageURL, currentRotation);
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

    // Muestra la imagen inicial cargada o capturada.
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

    // Muestra las diferentes imágenes procesadas (puntos, triangulación, etc.).
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