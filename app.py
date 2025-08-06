import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template, send_file, session
from werkzeug.utils import secure_filename
from models.face_processor import FaceProcessor


app = Flask(__name__)
# La clave secreta es necesaria para manejar sesiones y mensajes
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DOWNLOAD_FOLDER'] = 'static/downloads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Asegúrate de que las carpetas de subida y descarga existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Inicializa el procesador de rostros
face_processor = FaceProcessor()

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_image_to_session(image, filename, folder):
    """Guarda una imagen en el servidor y su ruta en la sesión."""
    filepath = os.path.join(app.config[folder], filename)
    cv2.imwrite(filepath, image)
    return filepath

@app.route('/')
def index():
    """Ruta principal que renderiza la plantilla index.html."""
    return render_template('index.html')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Sube una imagen, la guarda como 'original.jpg' y devuelve su URL.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró el archivo en la solicitud'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    if file and allowed_file(file.filename):
        # Asegura un nombre de archivo seguro
        original_filename = secure_filename(file.filename)
        session['original_filename'] = original_filename
        
        # Guarda la imagen original
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'original.jpg')
        file.save(filepath)
        
        session['original_image_path'] = filepath
        
        return jsonify({'original_image_url': f'/static/uploads/original.jpg?v={os.path.getmtime(filepath)}'}), 200
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@app.route('/detect_points/<int:num_points>', methods=['POST'])
def detect_points(num_points):
    """
    Detecta puntos faciales en la imagen original, los guarda y devuelve las URLs.
    """
    image_path = session.get('original_image_path')
    if not image_path or not os.path.exists(image_path):
        return jsonify({'error': 'No hay imagen para procesar. Por favor sube una imagen primero.'}), 400
    
    # Carga la imagen original
    image = cv2.imread(image_path)
    
    # Crea una copia para la detección
    detected_image = image.copy()
    
    # Llama al procesador de rostros
    processed_image, landmarks, error = face_processor.detect_face_landmarks(detected_image)
    if error:
        return jsonify({'error': error}), 400
    
    session['landmarks'] = landmarks
    
    # Guarda la imagen con los puntos
    points_image_path = save_image_to_session(processed_image, 'detected_points.jpg', 'UPLOAD_FOLDER')
    
    # Guarda solo los puntos sobre fondo negro
    points_only_image = face_processor.draw_points_on_black_bg(image.shape, landmarks)
    points_only_path = save_image_to_session(points_only_image, 'points_only.jpg', 'UPLOAD_FOLDER')
    
    return jsonify({
        'detected_image_url': f'/static/uploads/detected_points.jpg?v={os.path.getmtime(points_image_path)}',
        'points_only_url': f'/static/uploads/points_only.jpg?v={os.path.getmtime(points_only_path)}'
    }), 200

@app.route('/triangulate_delaunay', methods=['POST'])
def triangulate_delaunay():
    """
    Aplica la triangulación de Delaunay en la imagen y devuelve las URLs.
    """
    image_path = session.get('original_image_path')
    landmarks = session.get('landmarks')
    if not image_path or not landmarks:
        return jsonify({'error': 'No se detectaron puntos faciales. Por favor, detecta los puntos primero.'}), 400
    
    # Carga la imagen original
    image = cv2.imread(image_path)

    # Crea una copia para la triangulación
    triangulated_image = image.copy()
    
    # Llama al procesador de rostros para la triangulación
    delaunay_image, error = face_processor.draw_delaunay_triangles(triangulated_image, landmarks)
    if error:
        return jsonify({'error': error}), 400
    
    # Guarda la imagen triangulada sobre la original
    triangulated_path = save_image_to_session(delaunay_image, 'triangulated_delaunay.jpg', 'UPLOAD_FOLDER')

    # Guarda solo la triangulación sobre fondo negro
    delaunay_only_image, error = face_processor.draw_delaunay_on_black_bg(image.shape, landmarks)
    delaunay_only_path = save_image_to_session(delaunay_only_image, 'delaunay_only.jpg', 'UPLOAD_FOLDER')

    return jsonify({
        'triangulated_image_url': f'/static/uploads/triangulated_delaunay.jpg?v={os.path.getmtime(triangulated_path)}',
        'triangulation_only_url': f'/static/uploads/delaunay_only.jpg?v={os.path.getmtime(delaunay_only_path)}'
    }), 200

@app.route('/rotate_and_reprocess_3d/<int:angleX>/<int:angleY>/<int:angleZ>', methods=['POST'])
def rotate_and_reprocess_3d(angleX, angleY, angleZ):
    """
    Rota la imagen actual, la reprocesa (triangula) y devuelve el resultado final.
    """
    image_path = session.get('original_image_path')
    if not image_path or not os.path.exists(image_path):
        return jsonify({'error': 'No hay imagen para rotar. Por favor sube una imagen primero.'}), 400
    
    # Carga la imagen original
    image = cv2.imread(image_path)
    
    # Llama a la nueva función del procesador de rostros para rotar en 3D
    rotated_image = face_processor.rotate_3d(image.copy(), angleX, angleY, angleZ)
    
    # Reprocesa la imagen rotada: detecta puntos y triangula.
    _, landmarks, error = face_processor.detect_face_landmarks(rotated_image)
    if error:
        # Si no se detecta el rostro después de la rotación, se devuelve la imagen rotada sin triangulación
        rotated_image_path = save_image_to_session(rotated_image, 'reprocessed_rotated.jpg', 'UPLOAD_FOLDER')
        return jsonify({
            'reprocessed_image_url': f'/static/uploads/reprocessed_rotated.jpg?v={os.path.getmtime(rotated_image_path)}'
        }), 200

    # Dibuja la triangulación sobre un fondo negro.
    final_image, _ = face_processor.draw_delaunay_on_black_bg(rotated_image.shape, landmarks)

    # Guarda el resultado final
    reprocessed_path = save_image_to_session(final_image, 'reprocessed_rotated.jpg', 'UPLOAD_FOLDER')

    return jsonify({'reprocessed_image_url': f'/static/uploads/reprocessed_rotated.jpg?v={os.path.getmtime(reprocessed_path)}'}), 200


@app.route('/download_image', methods=['GET'])
def download_image():
    """
    Permite descargar la última imagen procesada.
    """
    # Se busca la última imagen guardada, que será la triangulada y posiblemente rotada.
    download_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'reprocessed_rotated.jpg')
    if not os.path.exists(download_filepath):
        download_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'delaunay_only.jpg')
        if not os.path.exists(download_filepath):
             download_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'detected_points.jpg')
             if not os.path.exists(download_filepath):
                 download_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'original.jpg')
                 if not os.path.exists(download_filepath):
                    return "No hay imagen para descargar.", 404

    return send_file(download_filepath, as_attachment=True, download_name='imagen_procesada.jpg')

if __name__ == '__main__':
    app.run(debug=True)