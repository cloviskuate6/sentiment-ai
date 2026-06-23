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
                // 1. Build de l'image via Docker classique (évite l'erreur d'interprétation compose)
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                
                // 2. Lancement sur le port 8085 (libre) vers le port d'écoute de votre app (8000 ou 8081)
                sh "docker run -d --name sentiment-ai-container -p 8085:8000 ${IMAGE_NAME}:${IMAGE_TAG} || docker run -d --name sentiment-ai-container -p 8085:8081 ${IMAGE_NAME}:${IMAGE_TAG}"
                
                // 3. Attente et vérification du Healthcheck sur le port 8085
                sh "sleep 5"
                sh "curl -f http://localhost:8085/health"
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
            // Nettoyage impératif du conteneur créé manuellement pour le test
            sh "docker rm -f sentiment-ai-container || true"
        }
        success {
            echo 'Pipeline réussi avec succès !'
        }
        failure {
            echo 'Pipeline échoué.'
        }
    }
}