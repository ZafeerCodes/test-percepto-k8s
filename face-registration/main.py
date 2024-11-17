from qdrant_client import QdrantClient
from qdrant_client.http import models
import cv2
from typing import List, Dict
import os
import uuid
from datetime import datetime
import os
from detection_models import FaceDetector,YOLOv8FaceDetector,RetinaFaceDetector,MTCNNDetector
from embedding_models import FaceEmbedding,ArcFaceEmbedding,FaceNetEmbedding
import glob
import socket
from confluent_kafka import Producer
from types_face import Topics,ImageStatus,ImageFailureReason,StatusType,DetectionModels,EmbeddingModels
import json


detection_model = os.getenv("detection_model") or "yolov8"
embedding_model = os.getenv("embedding_model") or "facenet"
collection_name = os.getenv("collection_name") 
alignment = os.getenv("alignment") or True
collection_path = "/mnt/data/" + os.getenv("collection_path")


producer_conf = {
    'bootstrap.servers': '192.168.0.56:9092',
    'client.id': socket.gethostname()
}      
producer = Producer(producer_conf)


class FaceRegistrationSystem:
    
    def __init__(self, detector_name: str = None, embedding_model_name: str =None, yolo_model_path: str = None):
        # Initialize detector
        self.detector = self._get_detector(detector_name, yolo_model_path)
        # Initialize embedding model
        self.embedding_model = self._get_embedding_model(embedding_model_name)
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient("192.168.0.95", port=30005)

        
    def _get_detector(self, name: str, yolo_model_path: str = None) -> FaceDetector:
        detectors = {
            'yolov8': lambda: YOLOv8FaceDetector(yolo_model_path),
            'retinaface': RetinaFaceDetector,
            'mtcnn': MTCNNDetector
        }
        print("nmame",name)
        return detectors[name.lower()]()
    
    def _get_embedding_model(self, name: str) -> FaceEmbedding:
        embedding_models = {
            'facenet': FaceNetEmbedding,
            'arcface': ArcFaceEmbedding
        }
        return embedding_models[name.lower()]()
    

    def process_images(self, image_paths: List[str], collection_name: str) -> Dict[str, List[str]]:
        """
        Process a list of images and store face embeddings in QdrantDB
        Returns a dictionary with successful and failed image paths
        """
        results = {'success': [], 'failed': []}
        print("readt to proceed",image_paths,collection_name)
        # Create collection if it doesn't exist
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=512,  # Adjust based on embedding size
                    distance=models.Distance.COSINE
                )
            )
            print("collection created --------------")
        except Exception as e:
            print("wrong  path--------------",e)

        for image_path in image_paths:
            print("ready for images..................")
            try:
                # Read image
                image = cv2.imread(image_path)
                if image is None:
                    print("no image")
                    value = {
                        "type": StatusType.IMAGESTATUS.value,
                        "image_path":image_path,
                        "status": ImageStatus.FAILURE.value,
                        "reason": ImageFailureReason.NOIMAGE.value
                    }
                    producer.produce(Topics.JOBS.value,key=image_path, value=json.dumps(value))
                    producer.flush()
                    continue
                    
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                print("image is threr................")
                # Detect faces
                faces = self.detector.detect_faces(image)
                
                if not faces:
                    print("image good, no faces.......")
                    value = {
                        "type": StatusType.IMAGESTATUS.value,
                        "image_path":image_path,
                        "status": ImageStatus.FAILURE.value,
                        "reason": ImageFailureReason.NOFACES.value
                    }
                    producer.produce(Topics.JOBS.value,key=image_path, value=json.dumps(value))
                    producer.flush()
                    continue
                
                # Generate embeddings and store in Qdrant
                for idx, face in enumerate(faces):
                    try:
                        print("faces present")
                        embedding = self.embedding_model.generate_embedding(face)
                        
                        # Generate a unique ID (UUID)
                        point_id = str(uuid.uuid4())
                        
                        # Create payload with metadata
                        payload = {
                            "image_path": image_path,
                            "face_index": idx,
                            "timestamp": datetime.now().isoformat(),
                            "filename": os.path.basename(image_path)
                        }
                        
                        print("sending....")
                        # Store in Qdrant
                        self.qdrant_client.upsert(
                            collection_name=collection_name,
                            points=[
                                models.PointStruct(
                                    id=point_id,  # Using UUID string
                                    payload=payload,
                                    vector=embedding.tolist()
                                )
                            ]
                        )
                        print("sent....")
                    except Exception as e:
                        print("excapetion before sending.............")
                        results['failed'].append(f"{image_path} (face {idx}): {str(e)}")
                        continue
                
                value = {
                    "type": StatusType.IMAGESTATUS.value,
                    "image_path":image_path,
                    "status": ImageStatus.COMPLETED.value
                }
                producer.produce(Topics.JOBS.value,key=image_path, value=json.dumps(value))
                producer.flush()
                print("sent successfull images.........")
            except Exception as e:
                print("exception as e ",e)
                results['failed'].append(f"{image_path}: {str(e)}")
        print("-------------------------resytks",results)
        return results
    
    def search_similar_faces(
        self, 
        collection_name: str, 
        image_path: str, 
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for similar faces using a query image
        """
        try:
            # Read and process query image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read query image")
                
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.detector.detect_faces(image)
            if not faces:
                raise ValueError("No faces detected in query image")
            
            # Generate embedding for first face
            query_embedding = self.embedding_model.generate_embedding(faces[0])
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    'id': hit.id,
                    'score': hit.score,
                    'image_path': hit.payload.get('image_path'),
                    'face_index': hit.payload.get('face_index'),
                    'timestamp': hit.payload.get('timestamp'),
                    'filename': hit.payload.get('filename')
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching faces: {str(e)}")
            return []
    

    # Driver code for testing
def test_face_registration(detection_model:str,embedding_model:str,collection_name:str,alignment:bool,collection_path:str):
    system = FaceRegistrationSystem(DetectionModels.YOLOV8.value, EmbeddingModels.FACENET.value)
    image_paths = glob.glob(f"{collection_path}/*.jpeg") + glob.glob (f"{collection_path}/*.png") + glob.glob(f"{collection_path}/*.jpg")
    #Register faces
    results = system.process_images(
        image_paths=image_paths,
        collection_name=collection_name
    )
    print("Successfully processed images:")
    for img in results['success']:
        print(f"- {img}")
    
    #print("\nFailed to process images:")
    for img in results['failed']:
        print(f"- {img}")
    
    
if __name__ == "__main__":
    print("de",detection_model)
    print("de",embedding_model)
    print("de",collection_name)
    print("de",collection_path)
    test_face_registration(detection_model=detection_model,embedding_model=embedding_model,alignment=True,collection_name=collection_name,collection_path=collection_path)