pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "devaraj74/stayfinder-py"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS = "docker-cred"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/gcdevaraj/stayfinder-py.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                . venv/bin/activate

                if [ -d tests ]; then
                    pytest
                else
                    echo "No tests found. Skipping..."
                fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
                docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest
                '''
            }
        }

        stage('Scan Docker Image') {
            steps {
                sh '''
                trivy image $DOCKER_IMAGE:$DOCKER_TAG
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withDockerRegistry(credentialsId: "${DOCKER_CREDENTIALS}", url: "https://index.docker.io/v1/") {
    sh '''
    docker push $DOCKER_IMAGE:${DOCKER_TAG}
    docker push $DOCKER_IMAGE:latest
    '''
}
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully."
        }

        failure {
            echo "Pipeline failed."
        }

        always {
            cleanWs()
        }
    }
}
