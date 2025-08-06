import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from models.face_processor import FaceProcessor

# Configuración de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data_rostro'

# Almacenamiento temporal para la última imagen subida o capturada
last_image_path = None

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
    global last_image_path
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        last_image_path = filepath

        return jsonify({
            'success': True,
            'original_image_url': f'/uploaded_images/{filename}',
            'message': 'Imagen subida correctamente. Use los botones para procesar.'
        })

@app.route('/detect_points', methods=['POST'])
def detect_points():
    global last_image_path
    if not last_image_path or not os.path.exists(last_image_path):
        return jsonify({'error': 'No hay una imagen para procesar'}), 400
    
    image = cv2.imread(last_image_path)
    if image is None:
        return jsonify({'error': 'No se pudo cargar la imagen'}), 500
    
    # Procesar la imagen con la clase FaceProcessor (Modelo)
    processed_image, _, error = processor.detect_face_landmarks(image.copy())

    if error:
        return jsonify({'error': error}), 400

    filename = os.path.basename(last_image_path)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'detected_' + filename)
    cv2.imwrite(temp_path, processed_image)

    # Actualizar la ruta global para que apunte a la imagen procesada
    last_image_path = temp_path

    return jsonify({
        'success': True,
        'image_url': f'/uploaded_images/detected_{filename}',
        'message': 'Puntos faciales detectados.'
    })
    
@app.route('/triangulate_delaunay', methods=['POST'])
def triangulate_delaunay():
    global last_image_path
    if not last_image_path or not os.path.exists(last_image_path):
        return jsonify({'error': 'No hay una imagen para triangular'}), 400

    image = cv2.imread(last_image_path)
    if image is None:
        return jsonify({'error': 'No se pudo cargar la imagen'}), 500

    # Primero detectamos los puntos para la triangulación
    _, landmarks, error = processor.detect_face_landmarks(image.copy())
    if error:
        return jsonify({'error': error}), 400

    # Luego aplicamos la triangulación
    triangulated_image, error = processor.draw_delaunay_triangles(image.copy(), landmarks)
    if error:
        return jsonify({'error': error}), 400

    filename = os.path.basename(last_image_path)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'triangulated_' + filename)
    cv2.imwrite(temp_path, triangulated_image)
    
    # Actualizar la ruta global para que apunte a la imagen triangulada
    last_image_path = temp_path

    return jsonify({
        'success': True,
        'image_url': f'/uploaded_images/triangulated_{filename}',
        'message': 'Triangulación de Delaunay aplicada.'
    })

@app.route('/uploaded_images/<filename>')
def uploaded_file(filename):
    """
    Ruta para servir archivos desde la carpeta data_rostro.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download_image', methods=['GET'])
def download_image():
    global last_image_path
    if not last_image_path or not os.path.exists(last_image_path):
        return jsonify({'error': 'No hay una imagen para descargar'}), 400

    # Obtener el nombre del archivo de la última imagen procesada
    filename = os.path.basename(last_image_path)
    
    # Enviar el archivo para su descarga
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)