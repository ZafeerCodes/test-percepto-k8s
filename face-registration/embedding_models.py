
import numpy as np
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torchvision.transforms as transforms
from insightface import iresnet100  
 

class FaceEmbedding:
    """Base class for face embedding models"""
    def __init__(self):
        self.model = None
    
    def generate_embedding(self, face_image) -> np.ndarray:
        raise NotImplementedError

class FaceNetEmbedding(FaceEmbedding):
    def __init__(self):
        super().__init__()
        self.model = InceptionResnetV1(pretrained='vggface2').eval()
        self.transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    
    def generate_embedding(self, face_image) -> np.ndarray:
        if isinstance(face_image, np.ndarray):
            face_image = Image.fromarray(face_image)
        face_tensor = self.transform(face_image).unsqueeze(0)
        with torch.no_grad():
            embedding = self.model(face_tensor)
        return embedding.numpy().flatten()

class ArcFaceEmbedding:
    def __init__(self):
        self.model = iresnet100(pretrained=True).eval()  # Assuming an iresnet100 model for ArcFace
        self.transform = transforms.Compose([
            transforms.Resize((112, 112)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    def generate_embedding(self, face_image) -> np.ndarray:
        if isinstance(face_image, np.ndarray):
            face_image = Image.fromarray(face_image)
            face_tensor = self.transform(face_image).unsqueeze(0)
        with torch.no_grad():
            embedding = self.model(face_tensor)
        return embedding.numpy().flatten()