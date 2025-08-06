import cv2
import mediapipe as mp
import numpy as np

class FaceProcessor:
    def __init__(self):
        # Inicializa MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

    def detect_face_landmarks(self, image, desired_points_indices=None):
        """
        Detecta los 468 puntos faciales en una imagen usando MediaPipe
        y filtra para dibujar solo los puntos con los índices deseados.
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)

        landmarks_points = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, landmark in enumerate(face_landmarks.landmark):
                    # Solo procesa si el índice está en la lista de puntos deseados
                    # Si desired_points_indices es None, dibuja todos los puntos
                    if desired_points_indices is None or idx in desired_points_indices:
                        h, w, c = image.shape
                        cx, cy = int(landmark.x * w), int(landmark.y * h)
                        landmarks_points.append((cx, cy))
                        cv2.circle(image, (cx, cy), 1, (0, 255, 0), -1)

            return image, landmarks_points, None
        
        return image, None, "No se detectaron rostros."

    def draw_points_on_black_bg(self, image_shape, landmarks):
        """
        Dibuja los puntos faciales en una imagen de fondo negro.
        """
        black_bg = np.zeros(image_shape, dtype=np.uint8)
        if landmarks:
            for point in landmarks:
                cv2.circle(black_bg, point, 1, (0, 255, 0), -1)
        return black_bg

    def draw_delaunay_triangles(self, image, landmarks):
        """
        Dibuja los triángulos de Delaunay en la imagen original.
        """
        if not landmarks or len(landmarks) < 3:
            return image, "No hay suficientes puntos para la triangulación."
        
        delaunay_image = image.copy()
        rect = (0, 0, image.shape[1], image.shape[0])
        subdiv = cv2.Subdiv2D(rect)

        for p in landmarks:
            subdiv.insert((int(p[0]), int(p[1])))

        triangles = subdiv.getTriangleList()

        for t in triangles:
            pt1 = (int(t[0]), int(t[1]))
            pt2 = (int(t[2]), int(t[3]))
            pt3 = (int(t[4]), int(t[5]))
            cv2.line(delaunay_image, pt1, pt2, (0, 255, 0), 1)
            cv2.line(delaunay_image, pt2, pt3, (0, 255, 0), 1)
            cv2.line(delaunay_image, pt3, pt1, (0, 255, 0), 1)
        
        return delaunay_image, None
    
    def draw_delaunay_on_black_bg(self, image_shape, landmarks):
        """
        Dibuja los triángulos de Delaunay en una imagen de fondo negro.
        """
        black_bg = np.zeros(image_shape, dtype=np.uint8)
        if not landmarks or len(landmarks) < 3:
            return black_bg, "No hay suficientes puntos para la triangulación."
        
        rect = (0, 0, image_shape[1], image_shape[0])
        subdiv = cv2.Subdiv2D(rect)

        for p in landmarks:
            subdiv.insert((int(p[0]), int(p[1])))

        triangles = subdiv.getTriangleList()

        for t in triangles:
            pt1 = (int(t[0]), int(t[1]))
            pt2 = (int(t[2]), int(t[3]))
            pt3 = (int(t[4]), int(t[5]))
            cv2.line(black_bg, pt1, pt2, (0, 255, 0), 1)
            cv2.line(black_bg, pt2, pt3, (0, 255, 0), 1)
            cv2.line(black_bg, pt3, pt1, (0, 255, 0), 1)
        
        return black_bg, None
