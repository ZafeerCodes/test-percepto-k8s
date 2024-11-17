from enum import Enum
class DetectionModels(Enum):
    YOLOV8 = "yolov8"
    RETINAFACE = "retinaface"
    MTCNN = "mtcnn"

class EmbeddingModels(Enum):
    FACENET = "facenet"
    ARCFACE = "arcface"

class Topics(Enum):
    JOBS = "jobs"
class StatusType(Enum):
    IMAGESTATUS = "image-status"

class ImageStatus(Enum):
    COMPLETED = "completed"
    FAILURE = "faliure"

class ImageFailureReason(Enum):
    NOIMAGE = "Could not read Image"
    NOFACES = "No faces detected inside image"
