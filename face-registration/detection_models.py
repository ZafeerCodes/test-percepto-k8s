from typing import List
import numpy as np
from ultralytics import YOLO
from retinaface import RetinaFace
from facenet_pytorch import MTCNN
from PIL import Image


class FaceDetector:
    """Base class for face detection models"""
    def __init__(self):
        self.model = None
    
    def detect_faces(self, image) -> List[np.ndarray]:
        raise NotImplementedError

class YOLOv8FaceDetector(FaceDetector):
    def __init__(self, model_path: str = None):
        super().__init__()
        if model_path:
            self.model = YOLO(model_path)
        else:
            # Download YOLOv8n-face model if not provided
            self.model = YOLO('yolov8n-face (1).pt')
    
    def detect_faces(self, image) -> List[np.ndarray]:
        """
        Detect faces using YOLOv8 face detection model
        Args:
            image: numpy array of image in RGB format
        Returns:
            List of cropped face images
        """
        results = self.model(image, conf=0.5)  # Adjust confidence threshold as needed
        faces = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Add padding (optional)
                height, width = image.shape[:2]
                padding = 20
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(width, x2 + padding)
                y2 = min(height, y2 + padding)
                
                # Crop face
                face = image[y1:y2, x1:x2]
                if face.size > 0:  # Check if face crop is valid
                    faces.append(face)
        
        return faces


class RetinaFaceDetector(FaceDetector):
    def __init__(self):
        super().__init__()

    def detect_faces(self, image) -> List[np.ndarray]:
        faces = []
        resp = RetinaFace.detect_faces(image)  # Direct method call without instantiation
        if isinstance(resp, dict):
            for face in resp.values():
                box = face['facial_area']
                x1, y1, x2, y2 = map(int, box)
                face_img = image[y1:y2, x1:x2]
                faces.append(face_img)
        return faces

class MTCNNDetector(FaceDetector):
    def __init__(self):
        super().__init__()
        self.model = MTCNN(keep_all=True)
    
    def detect_faces(self, image) -> List[np.ndarray]:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        boxes, _ = self.model.detect(image)
        faces = []
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                face = np.array(image)[y1:y2, x1:x2]
                faces.append(face)
        return faces
