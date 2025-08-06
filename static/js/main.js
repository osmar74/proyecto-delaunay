document.addEventListener('DOMContentLoaded', () => {
    const btnIniciar = document.getElementById('btn-iniciar');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const inputUploadFile = document.getElementById('input-upload-file');
    const introMessage = document.getElementById('intro-message');

    btnIniciar.addEventListener('click', () => {
        sidebar.classList.toggle('show');
        mainContent.classList.toggle('pushed');
        if (sidebar.classList.contains('show')) {
            btnIniciar.textContent = 'Salir';
            if (introMessage) introMessage.style.display = 'none';
        } else {
            btnIniciar.textContent = 'Iniciar';
            if (introMessage) introMessage.style.display = 'block';
        }
    });

    // Event listener para el botón de "Subir Imagen"
    inputUploadFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadImage(file);
        }
    });

    async function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Mostrar un mensaje de carga
        mainContent.innerHTML = `
            <div class="intro-message">
                <h1>Procesando imagen...</h1>
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
                throw new Error(errorData.error || 'Error al procesar la imagen');
            }

            const result = await response.json();
            displayResults(file, result);

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

    function displayResults(originalFile, result) {
        mainContent.innerHTML = ''; // Limpia el contenido anterior

        const gridContainer = document.createElement('div');
        gridContainer.className = 'grid-container';

        // Cuadro para la imagen original
        const originalImageURL = URL.createObjectURL(originalFile);
        gridContainer.innerHTML += `
            <div class="result-container">
                <h2>Imagen Original</h2>
                <img src="${originalImageURL}" alt="Imagen Original">
            </div>
        `;

        // Cuadro para la imagen procesada
        gridContainer.innerHTML += `
            <div class="result-container">
                <h2>Rostro y Puntos Detectados</h2>
                <img src="${result.image_url}" alt="Imagen Procesada">
            </div>
        `;

        mainContent.appendChild(gridContainer);

        // Revoca la URL del objeto después de un tiempo para liberar memoria
        setTimeout(() => URL.revokeObjectURL(originalImageURL), 5000);
    }
});