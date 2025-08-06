import cv2
import mediapipe as mp
import numpy as np

class FaceProcessor:
    def __init__(self):
        # Inicializa MediaPipe Face Mesh para la detección de puntos faciales.
        # Usa static_image_mode=True porque procesamos imágenes estáticas, no video.
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

    def detect_face_landmarks(self, image, desired_points_indices=None):
        """
        Detecta los 468 puntos faciales en una imagen usando MediaPipe.
        
        Args:
            image (np.array): La imagen de entrada en formato BGR de OpenCV.
            desired_points_indices (list, optional): Una lista de índices de puntos 
                                                    faciales específicos a procesar.
                                                    Si es None, procesa todos.
        
        Returns:
            tuple: (processed_image, landmarks_points, error)
                   - processed_image: La imagen con los puntos dibujados.
                   - landmarks_points: Una lista de tuplas (x, y) con las coordenadas de los puntos.
                   - error: Un mensaje de error si no se detectan rostros, de lo contrario None.
        """
        # Convierte la imagen de BGR a RGB para MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)

        landmarks_points = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for idx, landmark in enumerate(face_landmarks.landmark):
                    h, w, c = image.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    landmarks_points.append((cx, cy))
                    cv2.circle(image, (cx, cy), 1, (0, 255, 0), -1)

            return image, landmarks_points, None
        
        return image, None, "No se detectaron rostros."

    def draw_points_on_black_bg(self, image_shape, landmarks):
        """
        Dibuja los puntos faciales detectados sobre una imagen de fondo negro.
        
        Args:
            image_shape (tuple): La forma (alto, ancho, canales) de la imagen original.
            landmarks (list): Una lista de tuplas (x, y) de los puntos faciales.
        
        Returns:
            np.array: Una imagen de fondo negro con los puntos dibujados.
        """
        black_bg = np.zeros(image_shape, dtype=np.uint8)
        if landmarks:
            for point in landmarks:
                cv2.circle(black_bg, point, 1, (0, 255, 0), -1)
        return black_bg

    def draw_delaunay_triangles(self, image, landmarks):
        """
        Dibuja los triángulos de Delaunay en la imagen original.
        
        Args:
            image (np.array): La imagen de entrada.
            landmarks (list): Una lista de tuplas (x, y) de los puntos faciales.

        Returns:
            tuple: (delaunay_image, error)
                   - delaunay_image: La imagen con la triangulación de Delaunay dibujada.
                   - error: Un mensaje de error si no hay suficientes puntos para la triangulación, de lo contrario None.
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
        
        Args:
            image_shape (tuple): La forma (alto, ancho, canales) de la imagen original.
            landmarks (list): Una lista de tuplas (x, y) de los puntos faciales.

        Returns:
            tuple: (black_bg, error)
                   - black_bg: Una imagen de fondo negro con la triangulación dibujada.
                   - error: Un mensaje de error si no hay suficientes puntos para la triangulación, de lo contrario None.
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

    def rotate_3d(self, image, angleX, angleY, angleZ):
        """
        Aplica rotaciones en los tres ejes (X, Y, Z) de una imagen.
        
        Args:
            image (np.array): La imagen de entrada.
            angleX (int): El ángulo de rotación en el eje X en grados.
            angleY (int): El ángulo de rotación en el eje Y en grados.
            angleZ (int): El ángulo de rotación en el eje Z en grados.

        Returns:
            np.array: La imagen rotada.
        """
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)

        # Rotación en el eje Z (rotación en el plano 2D)
        if angleZ != 0:
            M_z = cv2.getRotationMatrix2D(center, angleZ, 1.0)
            image = cv2.warpAffine(image, M_z, (w, h))

        # Rotación en el eje X e Y. Esto es una transformación de perspectiva.
        # Para simplificar, se implementa una rotación de perspectiva.
        # Esta es una aproximación y no una verdadera rotación 3D del modelo.
        if angleX != 0 or angleY != 0:
            f = 500  # Longitud focal
            (h, w) = image.shape[:2]
            cx, cy = center
            
            # Se crean los puntos 3D de la imagen
            pts_3d = np.array([
                [-w/2, -h/2, 0],
                [ w/2, -h/2, 0],
                [ w/2,  h/2, 0],
                [-w/2,  h/2, 0]
            ], dtype=np.float32)

            # Se aplican las rotaciones
            Rx = np.array([[1, 0, 0], [0, np.cos(np.radians(angleX)), -np.sin(np.radians(angleX))], [0, np.sin(np.radians(angleX)), np.cos(np.radians(angleX))]])
            Ry = np.array([[np.cos(np.radians(angleY)), 0, np.sin(np.radians(angleY))], [0, 1, 0], [-np.sin(np.radians(angleY)), 0, np.cos(np.radians(angleY))]])
            R = np.dot(Ry, Rx)
            
            pts_3d_rotated = np.dot(R, pts_3d.T).T

            # Se proyectan los puntos 3D de nuevo a 2D
            pts_2d_src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            pts_2d_dst = np.float32([
                [cx + f * pts[0] / (f + pts[2]), cy + f * pts[1] / (f + pts[2])] for pts in pts_3d_rotated
            ])
            
            M = cv2.getPerspectiveTransform(pts_2d_src, pts_2d_dst)
            image = cv2.warpPerspective(image, M, (w, h))

        return image

    def rotate_image(self, image, angle):
        """
        Rota una imagen alrededor de su centro (rotación 2D).
        
        Args:
            image (np.array): La imagen de entrada.
            angle (int): El ángulo de rotación en grados.

        Returns:
            np.array: La imagen rotada.
        """
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_image = cv2.warpAffine(image, M, (w, h))
        return rotated_image