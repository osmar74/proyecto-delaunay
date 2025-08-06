import cv2
import mediapipe as mp
import numpy as np

class FaceProcessor:
    """
    Clase para procesar imágenes, detectando 468 puntos faciales con MediaPipe
    y aplicando la triangulación de Delaunay.
    """
    def __init__(self):
        # Inicializa la clase de Face Mesh de MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

    def detect_face_landmarks(self, image):
        """
        Detecta los 468 puntos faciales en una imagen usando MediaPipe.
        Retorna la imagen con los puntos dibujados.
        """
        # Convertir la imagen a RGB, que es el formato que usa MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)

        landmarks_points = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, landmark in enumerate(face_landmarks.landmark):
                    h, w, c = image.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    landmarks_points.append((cx, cy))
                    # Dibuja un círculo en cada punto
                    cv2.circle(image, (cx, cy), 1, (0, 255, 0), -1)
            return image, landmarks_points, None
        
        return image, None, "No se detectaron rostros."

    def draw_delaunay_triangles(self, image, points):
        """
        Calcula y dibuja la triangulación de Delaunay sobre una imagen.
        """
        if not points:
            return image, "No hay puntos faciales para triangular."

        # Convierte los puntos a un formato compatible con OpenCV
        points_np = np.array(points)
        
        # Crea una copia de la imagen para dibujar los triángulos
        triangulated_image = image.copy()
        
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
            cv2.line(triangulated_image, pt1, pt2, (255, 255, 255), 1)
            cv2.line(triangulated_image, pt2, pt3, (255, 255, 255), 1)
            cv2.line(triangulated_image, pt3, pt1, (255, 255, 255), 1)

        return triangulated_image, None