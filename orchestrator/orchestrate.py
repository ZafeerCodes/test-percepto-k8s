print("inside again")
from kubernetes import client,config
from types_enums import  v1,Topics, ConsumeType,NameSpaces,FaceConf,LogMessage, TrainConf, PodStatusConf,ImageStatusConf
from confluent_kafka import Consumer
from kubernetes.client.rest import ApiException
from kafka_pipe import KafkaPipe
import json
import os

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

print("check.........")
kafkaInstance = KafkaPipe()
producer = kafkaInstance.producer
class Orchestrator:

    def get_pod(job_id:str,job_name:str):
        pod_name = f"{job_name}--{job_id}"
        namespace = NameSpaces.TRAINING.value
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=NameSpaces.TRAINING.value)
            print(f"Pod '{pod_name}' exists in namespace '{namespace}'.")
            return True
        except:
            print(f"Pod '{pod_name}' does not exist in namespace '{namespace}'.")
            return False

    def create_train_pod(job:TrainConf):

        pod_name = f"{job['job_name']}--{job['job_id']}"
        
        try:
            pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=pod_name,namespace=NameSpaces.TRAINING.value),
            spec=client.V1PodSpec(
                host_network=True,
                containers=[
                    client.V1Container(
                        name=pod_name,
                        image="zafeeruddin/train:latest",
                        command=["/bin/sh"],
                        args=["-c", "python /app/train.py"],
                        resources=client.V1ResourceRequirements(
                            limits={"nvidia.com/gpu": "1"}
                        ),
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/mnt/data",  # Path inside the container
                                name="nfs-storage"
                            ),
                            client.V1VolumeMount(
                                mount_path="/dev/shm",
                                name= "dshm"
                            )
                        ],
                        env=[
                            client.V1EnvVar(name="job_id", value=job["job_id"]),
                            client.V1EnvVar(name="job_name", value=job["job_name"]),
                            client.V1EnvVar(name="job_type", value=job["job_type"]),
                            client.V1EnvVar(name="type", value=job["type"]),
                            client.V1EnvVar(name="batch_size", value=str(job["batch_size"])),
                            client.V1EnvVar(name="epochs", value=str(job["epochs"])),
                            client.V1EnvVar(name="base_model", value=job["base_model"]),
                            client.V1EnvVar(name="dataset_path", value=job["dataset_path"]),
                            client.V1EnvVar(name="save_dir", value=job["save_dir"]),
                            client.V1EnvVar(name="status", value=job["status"])
                        ]
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="nfs-storage",
                        nfs=client.V1NFSVolumeSource(
                            server="192.168.0.62",
                            path="/home/tms-machine/Desktop/percepto/percepto-be/serve",
                            read_only=False  
                        )
                    ),
                    client.V1Volume(
                        name="dshm",
                        empty_dir=client.V1EmptyDirVolumeSource(
                            medium="Memory"
                        )                
                    )
                ],
                restart_policy="Never"
            )
            )

            try:
                api_instance = client.CoreV1Api()
                api_response = api_instance.create_namespaced_pod(
                namespace=NameSpaces.TRAINING.value,  # Change this to your namespace if necessary
                body=pod
                )
                print("Pod created. Status='%s'" % api_response.status.phase)
    
            except ApiException as e:
                if e.status == 401:
                    print("Authentication failed. Checking configuration...")
                    # Try to get current authentication info
                    try:
                        auth_info = v1.api_client.configuration.get_api_key_with_prefix('authorization')
                        print(f"Current auth configuration: {auth_info if auth_info else 'No auth info found'}")
                    except Exception as auth_e:
                        print(f"Error getting auth info: {auth_e}")
                raise e
        except ApiException as e:
                print(f"Exception when creating pod: ({e.status})")
                print(f"Reason: {e.reason}")
                if hasattr(e, 'body'):
                    print(f"Response body: {e.body}")
                raise
        except Exception as e:
            print(f"Other error occurred: {e}")
            raise
        
        return
 
    def register_faces(faceConf:FaceConf):
        collection_name = faceConf["collection_name"]
        collection_path = faceConf["collection_path"]
        alignment = faceConf["alignment"]
        detection_model = faceConf["detection_model"]
        embedding_model = faceConf["embedding_model"]
        job_type = faceConf["type"]
        pod_name = collection_name + "--" + "face-registration"
        

        try:
            pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=pod_name,namespace=NameSpaces.FACEREGISTRATION.value),
            spec=client.V1PodSpec(
                host_network=True,
                containers=[
                    client.V1Container(
                        name=pod_name,
                        image="zafeeruddin/face-registeration:latest",
                        command=["/bin/sh"],
                        args=["-c", "python /app/main.py"],
                        resources=client.V1ResourceRequirements(
                            limits={"nvidia.com/gpu": "1"}
                        ),
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/mnt/data",  # Path inside the container
                                name="nfs-storage"
                            ),
                            client.V1VolumeMount(
                                mount_path="/dev/shm",
                                name= "dshm"
                            )
                        ],
                        env=[
                            client.V1EnvVar(name="alignment", value=str(alignment)),
                            client.V1EnvVar(name="collection_path", value=collection_path),
                            client.V1EnvVar(name="collection_name", value=collection_name),
                            client.V1EnvVar(name="type", value=job_type),
                            client.V1EnvVar(name="embedding_model", value=embedding_model),
                            client.V1EnvVar(name="detection_model", value=detection_model)
                        ]
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="nfs-storage",
                        nfs=client.V1NFSVolumeSource(
                            server="192.168.0.62",
                            path="/home/tms-machine/Desktop/percepto/percepto-be/serve",
                            read_only=False  
                        )
                    ),
                    client.V1Volume(
                        name="dshm",
                        empty_dir=client.V1EmptyDirVolumeSource(
                            medium="Memory"
                        )                
                    )
                ],
                restart_policy="Never"
            )
            )
            api_instance = client.CoreV1Api()
            api_response = api_instance.create_namespaced_pod(
            namespace=NameSpaces.FACEREGISTRATION.value,  # Change this to your namespace if necessary
            body=pod
            )
            print("Pod created. Status='%s'" % api_response.status.phase)

        except Exception as e:
            print("Exception creating pod ",e)

    def produce_pod_status(self,pod_status:PodStatusConf):
        print("producing pods status")
        producer.produce(Topics.PODSTATUS.value, key=pod_status["job_id"], value=json.dumps(pod_status))
        producer.flush()
        return True
    
    def produce_image_status(self,image_status:ImageStatusConf):
        try:
            image_path = image_status["image_path"]
            status = json.dumps(image_status)
            producer.produce(Topics.IMAGESTATUS.value, key=image_path, value=status)
            producer.flush()
            return True
        except Exception as e:
            print("Exception producing image status ",e)

    def produce_logs(self,log_message:LogMessage):
        if log_message:
            directory_path = f"/mnt/data/TrainingLogs/{log_message['training_job_id']}"
            if not os.path.exists(directory_path):
                os.mkdir(directory_path)
            
            log_file_path = f"{directory_path}/log.txt"
            
            if not os.path.exists(log_file_path):
                log_file_path = os.path.join(directory_path, "logs.txt")
            
            with open(log_file_path,"a") as log_file:
                log_file.write(log_message["log"])
            
            producer.produce(ConsumeType.LOGSTATUS.value, key=log_message["training_job_id"],value=json.dumps(log_message))
            
    """
    1) Checks for any job to be scheduled
    2) If job required to be scheduled, create job then add id in pod_statuses
    3) Runs a loop thorough pods statuses
    4) Update if status is changed.
    5) Publishes update to server.
    """


consumer_conf = {
            'bootstrap.servers': '192.168.0.56:9092',
            'group.id': 'my-app4',
            'auto.offset.reset': 'earliest' , # Set to 'earliest' for debugging
            'socket.connection.setup.timeout.ms':120000,

        }

consumer = Consumer(consumer_conf)
consumer.subscribe([Topics.JOBS.value])

orchestrator = Orchestrator()
while True:

    # Consume jobs, status
    try:
        msg = consumer.poll(1.0)
        print("msg now",msg)
        if msg:
            produce = json.loads(msg.value().decode('utf-8'))
            print(produce)
            if produce["type"] == ConsumeType.TRAINING.value:
                job = produce
                job_id = job["job_id"]
                job_name = job["job_name"]
                if not Orchestrator.get_pod(job_id=job_id,job_name=job_name):
                    Orchestrator.create_train_pod(job)
            elif produce["type"] == ConsumeType.PODSTATUS.value :
                new_status:PodStatusConf = produce
                orchestrator.produce_pod_status(pod_status=new_status)
            elif produce["type"] == ConsumeType.IMAGESTATUS.value :
                new_status:ImageStatusConf = produce
                orchestrator.produce_image_status(image_status=new_status)
            elif produce["type"] == ConsumeType.FACEREGISTERATION.value:
                produce:FaceConf = produce
                Orchestrator.register_faces(produce)
            elif produce["type"] == ConsumeType.LOGSTATUS.value:
                produce:LogMessage = produce
                orchestrator.produce_logs(log_message=produce)

    except Exception as e:
        print("Excaeption ",e)
   
        
    

