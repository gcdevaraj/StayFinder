pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "devaraj74/stayfinder-py"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS = "docker-cred"
        GITHUB_CREDENTIALS = "github-cred"
    }

    stages {

       

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

stage('Update GitOps Repository') {
    steps {
        dir('gitops') {
            git branch: 'main',
                credentialsId: "${GITHUB_CREDENTIALS}",
                url: 'https://github.com/gcdevaraj/stayfinder-gitops.git'

            sh """
                sed -i 's|image: .*|image: ${DOCKER_IMAGE}:${DOCKER_TAG}|g' k8s/deployment.yaml

                git config user.name "Jenkins"
                git config user.email "jenkins@example.com"

                git add k8s/deployment.yaml
                git commit -m "Update image to ${DOCKER_TAG}" || true
                git push origin main
            """
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
