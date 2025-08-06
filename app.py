import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from models.face_processor import FaceProcessor

# Configuración de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data_rostro'

# Asegurarse de que la carpeta de subidas exista
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Inicializar la clase de procesamiento de rostros
processor = FaceProcessor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Cargar la imagen con OpenCV
        image = cv2.imread(filepath)
        if image is None:
            return jsonify({'error': 'No se pudo cargar la imagen'}), 500

        # Procesar la imagen con la clase FaceProcessor (Modelo)
        processed_image, landmarks, error = processor.detect_face_landmarks(image.copy())

        if error:
            return jsonify({'error': error}), 400

        # Guardar la imagen procesada temporalmente
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
        cv2.imwrite(temp_path, processed_image)

        return jsonify({
            'success': True,
            'original_image_url': f'/uploaded_images/{filename}',
            'processed_image_url': f'/uploaded_images/processed_{filename}',
            'landmarks_count': len(landmarks) if landmarks else 0
        })

@app.route('/uploaded_images/<filename>')
def uploaded_file(filename):
    """
    Ruta para servir archivos desde la carpeta data_rostro.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)