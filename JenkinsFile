def DOCKER_REGISTRY = "docker.io"
def DOCKER_USER_NAME = "zafeeruddin"
def DOCKER_USER_PASSWORD = credentials("docker-hub-credentials")
def KUBE_CONFIG = credentials("kubeconfig")
def GITHUB_REPO = credentials("https://github.com/masterworks-engineering/k8s-percepto")
def DEPLOYMENT_SERVICES = ['orchestrator', 'status', 'logger', 'qdrant']
def ONDEMAND_SERVICES = ['training', 'face-registrations']


def SERVICE_IMAGE_MAP = [
    'orchestrator': 'zafeeruddin/orch',
    'status': 'zafeeruddin/status',
    'logger': 'zafeeruddin/logger',
    'training': 'zafeeruddin/training',
    'face-registrations': 'zafeeruddin/faceregistrations'
]

pipeline{
    agent any
    
    environment{
        DOCKER_CREDENTIALS = credentials("docker-hub-credentials")
         KUBE_CONFIG = credentials("kubeconfig")
    }

    stages {
        stage("checkout"){
            steps{
                checkout scm
            }
        }
        stage("Detect changes"){
            steps{
                script{
                    def changes = sh(
                        script: "git diff --name only HEAD-1 HEAD"
                        returnStdout: true
                    ).trim()

                    env.CHANGED_SERVICES = ""
                    (DEPLOYMENT_SERVICES + ONDEMAND_SERVICES).each {
                        service ->
                            if(changes.contains(service + "/")){
                                env.CHANGED_SERVICES = service + " "
                            }
                    }

                    echo "Changed services: ${env.CHANGED_SERVICES}"
                }
            }
        }

        stage("Build and push to docker hub"){
            steps{
                script{
                    sh """
                            echo ${DOCKER_CREDENTIALS_PSW} | docker login ${DOCKER_REGISTRY} -u ${DOCKER_CREDENTIALS_USR} --password-stdin
                        """

                    env.CHANGED_SERVICES.trim().split(" ").each {service ->
                        if (service  && service!="qdrant"){
                            dir(service){
                                def imageName = SERVICE_IMAGE_MAP[service]
                                def imageTag = "${imageName}"
                                
                                sh """
                                    docker build -t ${imageTag} .
                                    docker push ${imageTag}
                                """
                                echo "Build and published docker image with ${imageTag}"
                            }
                        }    
                    }
                }
            }
        }
        
        stage("Deploy changes to k8s"){
            steps{
                script{
                    env.CHANGED_SERVICES.trim().split(" ").each{service ->
                        if(DEPLOYMENT_SERVICES.contains(service)){
                               sh """
                                kubectl --kubeconfig=${KUBECONFIG} rollout restart deployment ${service}-deployment
                                kubectl --kubeconfig=${KUBECONFIG} rollout status deployment ${service}-deployment
                            """
                        }else if(ONDEMAND_SERVICES.contains(service)){
                            sh """
                                kubectl --kubeconfig=${KUBECONFIG} apply -f ${service}/k8s-manifest.yaml
                            """
                        }
                    }   
                }
            }
        }
    }

    post{
        always{
            sh "docker logout ${DOCKER_REGISTRY}"
            cleanWs()
        }
        success{
            echo "Pipeline Successfull!"
            script {
                if (env.CHANGED_SERVICES) {
                    def message = "Successfully updated services: ${env.CHANGED_SERVICES}"
                    echo message
                }
            }
        }
        failure {
            echo 'Pipeline failed! Please check the logs.'
        }
    }
}