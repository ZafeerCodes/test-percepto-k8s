import json
from enum import Enum
from confluent_kafka import Producer,Consumer
import socket
from types_enums import new_jobs,pod_stauses,client,PodStatusTypes


class Topics(Enum):
    JOBS = "jobs"
    PODSTATUS = "pod_status"
    IMAGESTATUS="image_status"

class KafkaPipe:
    def __init__(self) -> None:
        producer_conf = {
            'bootstrap.servers': '192.168.0.56:9092',
            'client.id': socket.gethostname()
        }
        
        consumer_conf = {
            'bootstrap.servers': '192.168.0.56:9092',
            'group.id': 'job-newest',
            'auto.offset.reset': 'latest'  # Set to 'earliest' for debugging
        }
        self.producer = Producer(producer_conf)
        self.consumer = Consumer(consumer_conf)

    def acked(self,err,msg):
        if err is not None:
            print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
        else:
            print("Message produced: %s" % (str(msg)))
    
    

    def get_job(self):
        job = new_jobs.get()
        if job:
            return job
    
    def get_consumer(self)->Consumer:
        return self.consumer
    
    def consume_jobs(self):
        print("Starting to consume messages...",Topics.JOBS.value)
        self.consumer.subscribe([Topics.JOBS.value])

        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue    
            if msg.error():
                # Log specific error for debugging
                print("End of partition reached {}/{}".format(msg.topic(), msg.partition()))
                continue
            
            # Decode and process the message
            print('Received message: {}'.format(msg.value().decode('utf-8')))
            try:
                # Try parsing the message to JSON
                message_data = json.loads(msg.value().decode('utf-8'))
                print("msg is now dict", type(message_data))
            except json.JSONDecodeError:
                print("Error decoding message as JSON")
                message_data = msg.value().decode('utf-8')
            new_jobs.put(message_data)


    def get_status(job_id,job_name)-> str:

        pod_name = f"{job_name}-{job_id}"
        try:
            api_instance = client.CoreV1Api()
            pod = api_instance.read_namespaced_pod(name=pod_name,namespace="default")
            # pod = v1.read_namespaced_pod()
            if not pod:
                return PodStatusTypes.ERROR.value
            new_pod_status = pod.status.phase
            return new_pod_status
        except:
            print("error")
    def set_status(key,status):
            kafka_instance = KafkaPipe() 
            kafka_instance.produce_status(key,status)
    

if __name__ == "__main__":
    kafka_instance = KafkaPipe()
    msg = kafka_instance.consume_jobs()
    print("got a message ",msg)
    print("u got anythibng")
    while True:
        for pod in pod_stauses:
            job_id = pod["job_id"]
            job_name = pod["job_name"]
            old_status = pod["status"]

            try:
                new_pod_status = KafkaPipe.get_status(job_id,job_name)
                if new_pod_status!=old_status:
                    KafkaPipe.set_status(job_id,new_pod_status)
            except:
                print("Unable to update status")        
    