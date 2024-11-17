from types_enums import  Job
from kubernetes import client,watch
from types_enums import v1,Job
import os 
class Logger:
    def __init__(self, namespace="default"):
        self.namespace = namespace
        os.makedirs("logs", exist_ok=True)


    def write_log(job:Job):
        while True:
            try:
                w = watch.Watch()
                pod_name = f"{job['job_name']}-{job['job_id']}"
                for log in w.stream(v1.read_namespaced_pod_log, name=pod_name, namespace="default", follow=True):
                    with open(f"logs/{pod_name}.log","a") as file:
                        file.write(log + "\n    ")
                    print(f"Logs from pod {pod_name} have been written to pod.log")
            except client.ApiException as e:
                    print(f"Exception when trying to stream logs from {pod_name}: {e}")
                    continue
