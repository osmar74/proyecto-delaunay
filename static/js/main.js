document.addEventListener('DOMContentLoaded', () => {
    const btnIniciar = document.getElementById('btn-iniciar');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const btnSalir = document.createElement('button'); // Creamos el botón "Salir"

    btnSalir.textContent = 'Salir';
    btnSalir.className = 'menu-item';

    let sidebarVisible = false;

    btnIniciar.addEventListener('click', () => {
        if (!sidebarVisible) {
            sidebar.classList.add('show');
            mainContent.classList.add('pushed');
            btnIniciar.textContent = 'Salir';
            sidebarVisible = true;
            // Puedes añadir el botón de "Salir" aquí o en el header
        } else {
            sidebar.classList.remove('show');
            mainContent.classList.remove('pushed');
            btnIniciar.textContent = 'Iniciar';
            sidebarVisible = false;
        }
    });

    // Event listener para el botón de "Subir Imagen"
    const inputUploadFile = document.getElementById('input-upload-file');
    inputUploadFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            console.log('Archivo seleccionado:', file.name);
            // Aquí llamaremos a la función para subir la imagen al servidor
            // uploadImage(file);
            // Por ahora, solo mostraremos la imagen en el main
            const reader = new FileReader();
            reader.onload = (e) => {
                displayImage(e.target.result, 'Imagen Subida');
            };
            reader.readAsDataURL(file);
        }
    });

    // Función para mostrar la imagen en el contenedor principal
    function displayImage(imageUrl, title) {
        const mainContent = document.querySelector('.main-content');
        mainContent.innerHTML = ''; // Limpia el contenido anterior

        const imageContainer = document.createElement('div');
        imageContainer.className = 'result-container';

        const titleElement = document.createElement('h2');
        titleElement.textContent = title;

        const imageElement = document.createElement('img');
        imageElement.src = imageUrl;
        imageElement.alt = title;

        imageContainer.appendChild(titleElement);
        imageContainer.appendChild(imageElement);
        mainContent.appendChild(imageContainer);
    }
});