import os
import cv2
import numpy as np
import random
from flask import Flask, render_template, request, jsonify, send_from_directory
from models.face_processor import FaceProcessor

# Configuración de Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data_rostro'

# Almacenamiento temporal para la última imagen subida o capturada
last_image_path = None
# Guarda los puntos detectados para la triangulación
last_landmarks = None

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
            'message': 'Imagen subida correctamente. Usa los botones para procesar.'
        })

@app.route('/detect_points/<int:num_points>', methods=['POST'])
def detect_points(num_points):
    global last_image_path, last_landmarks
    if not last_image_path or not os.path.exists(last_image_path):
        return jsonify({'error': 'No hay una imagen para procesar'}), 400
    
    image = cv2.imread(last_image_path)
    if image is None:
        return jsonify({'error': 'No se pudo cargar la imagen'}), 500
    
    # Generar una lista aleatoria de puntos a partir de los 468 disponibles
    all_points = list(range(468))
    if num_points > 468:
        num_points = 468
    desired_points_indices = random.sample(all_points, num_points)

    processed_image, landmarks, error = processor.detect_face_landmarks(image.copy(), desired_points_indices)
    if error:
        return jsonify({'error': error}), 400
    
    last_landmarks = landmarks # Guardar los landmarks para la triangulación
    points_only_image = processor.draw_points_on_black_bg(image.shape, landmarks)
    
    filename = os.path.basename(last_image_path)
    detected_path = os.path.join(app.config['UPLOAD_FOLDER'], f'detected_{num_points}_' + filename)
    points_only_path = os.path.join(app.config['UPLOAD_FOLDER'], f'points_only_{num_points}_' + filename)
    
    cv2.imwrite(detected_path, processed_image)
    cv2.imwrite(points_only_path, points_only_image)

    return jsonify({
        'success': True,
        'original_image_url': f'/uploaded_images/{filename}',
        'detected_image_url': f'/uploaded_images/detected_{num_points}_{filename}',
        'points_only_url': f'/uploaded_images/points_only_{num_points}_{filename}',
        'message': f'Puntos faciales ({num_points}) detectados.'
    })
    
@app.route('/triangulate_delaunay', methods=['POST'])
def triangulate_delaunay():
    global last_image_path, last_landmarks
    if last_landmarks is None:
        return jsonify({'error': 'Primero detecta los puntos faciales.'}), 400

    image = cv2.imread(last_image_path)
    if image is None:
        return jsonify({'error': 'No se pudo cargar la imagen'}), 500
    
    filename = os.path.basename(last_image_path).split('_')[-1] # Obtiene el nombre original del archivo
    num_points = os.path.basename(last_image_path).split('_')[1] # Obtiene el número de puntos del nombre del archivo

    triangulated_image, error = processor.draw_delaunay_triangles(image.copy(), last_landmarks)
    if error:
        return jsonify({'error': error}), 400
        
    triangulation_only_image, error = processor.draw_delaunay_on_black_bg(image.shape, last_landmarks)
    if error:
        return jsonify({'error': error}), 400

    triangulated_path = os.path.join(app.config['UPLOAD_FOLDER'], f'triangulated_{num_points}_' + filename)
    triangulation_only_path = os.path.join(app.config['UPLOAD_FOLDER'], f'triangulation_only_{num_points}_' + filename)
    
    cv2.imwrite(triangulated_path, triangulated_image)
    cv2.imwrite(triangulation_only_path, triangulation_only_image)
    
    return jsonify({
        'success': True,
        'original_image_url': f'/uploaded_images/{filename}',
        'detected_image_url': f'/uploaded_images/detected_{num_points}_{filename}',
        'triangulated_image_url': f'/uploaded_images/triangulated_{num_points}_{filename}',
        'points_only_url': f'/uploaded_images/points_only_{num_points}_{filename}',
        'triangulation_only_url': f'/uploaded_images/triangulation_only_{num_points}_{filename}',
        'message': 'Triangulación de Delaunay aplicada.'
    })

@app.route('/uploaded_images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download_image', methods=['GET'])
def download_image():
    global last_image_path
    if not last_image_path or not os.path.exists(last_image_path):
        return jsonify({'error': 'No hay una imagen para descargar'}), 400

    filename = os.path.basename(last_image_path)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)