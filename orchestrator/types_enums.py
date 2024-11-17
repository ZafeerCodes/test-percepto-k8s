
from enum import Enum
from kubernetes import client
import queue

class NameSpaces(Enum):
    DEFAULT = "default"
    TRAINING = "training"
    FACEREGISTRATION = "faceregistrations"


class Topics(Enum):
    JOBS = "jobs"
    PODSTATUS = "pod-status"
    IMAGESTATUS = "image-status"

class JobType(Enum):
    CLASSIFICATION = "CLASSIFICATION"
    SEGMENTATION = "SEGMENTATION"
    DETECTION = "DETECTION"

class YOLODetectionModels(Enum):
    YOLOV8N = "yolov8n.pt"
    YOLOV8S = "yolov8s.pt"
    YOLOV8M = "yolov8m.pt"
    YOLOV8L = "yolov8l.pt"
    YOLOV8X = "yolov8x.pt"

class YOLOSegmentationModels(Enum):
    YOLOV8N_SEG = "yolov8n-seg.pt"
    YOLOV8S_SEG = "yolov8s-seg.pt"
    YOLOV8M_SEG = "yolov8m-seg.pt"
    YOLOV8L_SEG = "yolov8l-seg.pt"
    YOLOV8X_SEG = "yolov8x-seg.pt"

class YOLOClassificationModels(Enum):
    YOLOV8N_CLS = "yolov8n-cls.pt"
    YOLOV8S_CLS = "yolov8s-cls.pt"
    YOLOV8M_CLS = "yolov8m-cls.pt"
    YOLOV8L_CLS = "yolov8l-cls.pt"
    YOLOV8X_CLS = "yolov8x-cls.pt"

class PodStatusTypes(Enum):
    PROCESSING = "processing"
    QUEUED = "queued"
    RUNNING = "Running"
    PENDING = "Pending"
    COMPLETED = "Completed"
    SUCCESSFULL = "Successful"
    ERROR = "Error"

class ImageStatusTypes(Enum):
    COMPLETED = "completed"
    PROCESSING = "processing"
    ERROR = "error"

class ConsumeType(Enum):
    TRAINING = "TRAINING"
    FACEREGISTERATION = "FACE-REGISTRATION"
    PODSTATUS = "pod-status"
    IMAGESTATUS = "image-status"
    LOGSTATUS = "log-status"

from typing import TypedDict

class LogMessage(TypedDict):
    training_job_id: str
    training_job_name: str
    log: str



class TrainConf(TypedDict):
    job_id: str
    job_name: str
    job_type: JobType
    type: ConsumeType.TRAINING.value
    epochs: int
    batch_size: int
    base_model: str
    dataset_path: str
    save_dir: str
    status: PodStatusTypes
    
class FaceConf(TypedDict):
    type: ConsumeType.FACEREGISTERATION.value
    collection_path: str
    collection_name: str
    embedding_model: str
    detection_model: str
    alignment: bool


class ImageStatusConf(TypedDict):
    type: ConsumeType.IMAGESTATUS.value
    image_path: str
    status: ImageStatusTypes

class PodStatusConf(TypedDict):
    job_id: str
    job_name: str
    type: ConsumeType.PODSTATUS.value
    status: PodStatusTypes

    
v1 = client.CoreV1Api()

new_jobs = queue.Queue()
pod_stauses = []