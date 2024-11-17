
import json
from types_status import StatusType,PodStatus,NameSpaces,ImageStatus,Topics
from confluent_kafka import Producer,Consumer
import socket
from kubernetes import client,config
from kubernetes.client import ApiException
import time
try:
    config.load_incluster_config()
except:
    config.load_kube_config()


class KafkaPipe:
    def __init__(self) -> None:
        producer_conf = {
            'bootstrap.servers': '192.168.0.56:9092',
            'client.id': socket.gethostname()
        }
        self.producer = Producer(producer_conf)
        self.pod_statuses= []
        self.v1 = client.CoreV1Api()


    def remove_fr_pods(self):
        try:
            pods = self.v1.list_namespaced_pod(namespace=NameSpaces.FACEREGISTRATIONS.value)
            for pod in pods.items:
                if pod.status.phase == PodStatus.COMPLETED.value or  pod.status.phase==PodStatus.SUCCEEDED.value:
                    self.v1.delete_namespaced_pod(name=pod.metadata.name,namespace=NameSpaces.FACEREGISTRATIONS.value)
                    print("deleted pod inside fr ",pod.metatdata.name)
        except Exception as e:
            print("Error deleting pod in fr ",e)


    def remove_pod_arr(self,job_id:str):
        self.pod_statuses = [d for d in self.pod_statuses if d["job_id"] != job_id]
        print("item removed!",job_id)

    def acked(self,err,msg):
        if err is not None:
            print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
        else:
            print("Message produced: %s" % (str(msg)))
    
    def get_pod(self,job_id,job_name):
        pod_name = f"{job_name}-{job_id}"
        namespace = NameSpaces.TRAINING.value
        try:
        # Check if the pod exists by trying to get its details
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            print(f"Pod '{pod_name}' exists in namespace '{namespace}'.")
            return True
        except:
            print(f"Pod '{pod_name}' does not exist in namespace '{namespace}'.")
            return False
        
    def split_pod_name(self, pod_name: str):
        first_part, second_part = pod_name.split('--', 1)
        return first_part, second_part

    def remove_pod(self,pod_name:str):
        try:
            self.v1.delete_namespaced_pod(name=pod_name,namespace=NameSpaces.TRAINING.value)
            print("deleted pod ",pod_name)
        except ApiException as e:
            if e.status == 404:
                print("pod already deleted .......",pod_name)
        return True
    def get_status(self, job_id: str, job_name: str, namespace: str) -> str:
        pod_name = f"{job_name}--{job_id}"
        print("\n\n getting old status for ",pod_name)
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            print("new status is",pod.status.phase)
            return pod.status.phase
        except ApiException as e:
            if e.status == 404:
                print("pod not present ",job_id)
                self.remove_pod_arr(job_id)
                return PodStatus.ERROR.value

            print(f"Error getting pod status: {e}")
            return PodStatus.ERROR.value


    def get_pods(self,namespace:str):
        print("\n\n................................... check again....................")
        try:
            pods = self.v1.list_namespaced_pod(namespace=namespace)
            for pod in pods.items:
                job_name,job_id = self.split_pod_name(pod.metadata.name)

                value = {
                    "job_id":job_id,
                    "job_name":job_name,
                    "type":StatusType.POD.value,
                    "status":pod.status.phase
                }
                if value not in self.pod_statuses:
                    print("adding for first time .............",value)
                    self.pod_statuses.append(value)
                    status_update = {
                        "job_id": job_id,
                        "job_name": job_name,
                        "type": StatusType.POD.value,
                        "status": pod.status.phase
                    }
                    print("sending status for first time..........")
                    self.produce_status(key=job_id, status=status_update)
                elif pod.status.phase == PodStatus.COMPLETED.value or pod.status.phase == PodStatus.SUCCEEDED.value:
                    print("removing pod as already present..............")
                    self.remove_pod(pod.metadata.name)
                    self.remove_pod_arr(job_id)
                    print("new array ..................",self.pod_statuses)
            return
        except client.exceptions.ApiException as e:
            print(f"Exception when listing pods: {e}")
            return

    def produce_status(self,key:str,status:dict):
        print("producing status for ", status)
        if status["type"] == StatusType.POD.value:
            value = json.dumps(status)
            self.producer.produce(Topics.JOBS.value, key=key, value=value)
            self.producer.flush()

kafkaInstance = KafkaPipe()

while True:
    print("done with all try again")
    pod_statuses= kafkaInstance.pod_statuses
    kafkaInstance.get_pods(namespace=NameSpaces.TRAINING.value)
    for pod in pod_statuses:
        id = pod["job_id"]
        name = pod["job_name"]
        old_status = pod["status"]
        try:
            new_pod_status = kafkaInstance.get_status(
                job_id=id,
                job_name=name,
                namespace=NameSpaces.TRAINING.value
            )
            print("old status .... new status.......",old_status,new_pod_status)
            if  new_pod_status != old_status and new_pod_status!=PodStatus.ERROR.value:
                print("change in status ",old_status,new_pod_status)
                status_update = {
                    "job_id": id,
                    "job_name": name,
                    "type": StatusType.POD.value,
                    "status": new_pod_status
                }
                pod["status"] = new_pod_status
                kafkaInstance.produce_status(key=id, status=status_update)
        except Exception as e:
            print(f"Unable to update status: {e}")
    
    kafkaInstance.remove_fr_pods()

    time.sleep(2)
    
    