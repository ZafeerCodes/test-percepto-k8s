from enum import Enum
from kubernetes import client
from typing import TypedDict


class PodStatus(Enum):
    PROCESSING = "Processing"
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    ERROR = "Errored"
    SUCCEEDED = "Succeeded"
class NameSpaces(Enum):
    DEFAULT = "default"
    TRAINING = "training"
    FACEREGISTRATIONS = "faceregistrations"

class StatusType(Enum):
    IMAGE = "image-status"
    POD = "pod-status"
class Topics(Enum):
    JOBS = "jobs"
    PODSTATUS = "pod_status"
    IMAGESTATUS="image_status"

class Status(TypedDict):
    type: str
    status: str
    offset: str
    key: str

class ImageStatus(Status):
    collection_name:str  


