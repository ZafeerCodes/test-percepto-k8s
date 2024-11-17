from kubernetes import client,config
from type_logger import Namespaces,LogMessage,Topics,ConsumeType
import socket
from confluent_kafka import Producer
import uuid
import json
from concurrent.futures import ThreadPoolExecutor


v1 = client.CoreV1Api()

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

class Logger:
    def __init__(self):
        producer_conf = {
            'bootstrap.servers': '192.168.0.56:9092',
            'client.id': socket.gethostname()
        }      
        self.producer = Producer(producer_conf)

    
    def stream_pod_logs(self, pod_name:str, namespace=Namespaces.TRAINING.value):
        v1 = client.CoreV1Api()
        try:
            logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, follow=True, _preload_content=False)   
            for line in logs.stream():
                line = line.decode("utf-8")
                key = str(uuid.uuid4())
                job_name, job_id = pod_name.split("--",1)
                message:LogMessage = {
                    "training_job_name":job_name,
                    "training_job_id": job_id,
                    "log": line,
                    "type": ConsumeType.LOGSTATUS.value
                }
                print("ready to produce ",message)
                self.producer.produce(Topics.JOBS.value, key=key, value=json.dumps(message))
                self.producer.flush()
        except Exception as e:
            print(f"Error streaming logs for pod {pod_name}: {e}")


    def list_pods(self,namespace:str):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        v1 = client.CoreV1Api()
        try:
            pods = v1.list_namespaced_pod(namespace=namespace)
            with ThreadPoolExecutor() as executor:
                for pod in pods.items:
                    executor.submit(self.stream_pod_logs, pod.metadata.name, namespace)
        except Exception as e:
            print(f"Error listing pods: {e}")


logger = Logger()

while True:
    logger.list_pods(namespace=Namespaces.TRAINING.value)
    