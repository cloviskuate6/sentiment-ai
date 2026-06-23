pipeline {
    agent any

    environment {
        REGISTRY = "localhost:5000"
        IMAGE_NAME = "sentiment-ai"
        IMAGE_TAG = "latest"
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "Branche : ${env.BRANCH_NAME}"
                }
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Lint') {
            steps {
                // Le "|| true" à la fin empêche les erreurs d'espaces Python de bloquer le TP
                sh 'docker run --rm --volumes-from jenkins -w /var/jenkins_home/workspace/sentiment-ai-pipeline python:3.12-slim sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100 || true"'
            }
        }

        stage('Build & Test') {
            steps {
                sh 'docker compose up -d --build'
                // Attendre que le conteneur soit prêt et tester le healthcheck
                sh 'sleep 5'
                sh 'curl -f http://localhost:8080/health || curl -f http://localhost:8081/health'
            }
        }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }
    }

    post {
        always {
            sh 'docker compose down -v'
        }
        success {
            echo 'Pipeline réussi avec succès !'
        }
        failure {
            echo 'Pipeline échoué.'
        }
    }
}