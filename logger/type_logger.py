from typing import TypedDict
from enum import Enum


class ConsumeType(Enum):
    TRAINING = "TRAINING"
    FACEREGISTERATION = "FACE-REGISTRATION"
    PODSTATUS = "pod-status"
    IMAGESTATUS = "image-status"
    LOGSTATUS = "log-status"

class Topics(Enum):
    JOBS  = "jobs"

class JobType(Enum):
    CLASSIFICATION = "CLASSIFICATION"
    SEGMENTATION = "SEGMENTATION"
    DETECTION = "DETECTION"

class Namespaces(Enum):
    DEFAULT = "default"
    TRAINING = "training"
    FACEREGISTRATION = "face-registration"

class Job(TypedDict):
    job_id: str
    job_name: str
    job_type: JobType
    type: ConsumeType
    epochs: int
    batch_size: int
    base_model: str
    dataset_path: str
    save_dir: str
    status: str

class LogMessage(TypedDict):
    training_job_id: str
    training_job_name: str
    log: str

class Topics(Enum):
    JOBS = "jobs"

    