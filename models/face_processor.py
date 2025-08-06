import cv2
import dlib
import numpy as np

class FaceProcessor:
    """
    Clase para procesar imágenes, detectando puntos faciales y
    aplicando la triangulación de Delaunay.
    """
    def __init__(self):
        # Inicializa el detector de rostros de dlib
        self.detector = dlib.get_frontal_face_detector()
        # Carga el predictor de puntos faciales
        self.predictor = dlib.shape_predictor("models/data/shape_predictor_68_face_landmarks.dat")

    def detect_face_landmarks(self, image):
        """
        Detecta el rostro y los 68 puntos faciales en una imagen.
        Retorna la imagen con los puntos dibujados y el contorno del rostro.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        if not faces:
            return image, None, "No se detectaron rostros."

        for face in faces:
            # Dibuja el contorno del rostro
            x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)

            # Obtiene los 68 puntos faciales
            landmarks = self.predictor(gray, face)
            points = []
            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                points.append((x, y))
                # Dibuja un círculo en cada punto
                cv2.circle(image, (x, y), 2, (0, 255, 0), -1)

            return image, points, None

        return image, None, "No se detectaron rostros."

    def draw_delaunay_triangles(self, image, points):
        """
        Calcula y dibuja la triangulación de Delaunay sobre una imagen.
        """
        if not points:
            return image, "No hay puntos faciales para triangular."

        # Convierte los puntos a un formato compatible con OpenCV
        points_np = np.array(points)
        
        # Obtiene el rectángulo delimitador de los puntos
        rect = cv2.boundingRect(points_np)

        # Crea una subdivisión de Delaunay
        subdiv = cv2.Subdiv2D(rect)
        for p in points:
            subdiv.insert(p)

        # Obtiene los triángulos de Delaunay
        triangles = subdiv.getTriangleList()

        # Dibuja los triángulos en la imagen
        for t in triangles:
            pt1 = (int(t[0]), int(t[1]))
            pt2 = (int(t[2]), int(t[3]))
            pt3 = (int(t[4]), int(t[5]))
            cv2.line(image, pt1, pt2, (255, 255, 255), 1)
            cv2.line(image, pt2, pt3, (255, 255, 255), 1)
            cv2.line(image, pt3, pt1, (255, 255, 255), 1)

        return image, None