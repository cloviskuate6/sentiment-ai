// Jenkinsfile Pipeline CI/CD SentimentAI
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'sentiment-ai'
        REGISTRY   = 'ghcr.io/cloviskuate6'
        IMAGE_TAG  = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branche : ${env.BRANCH_NAME}"
                echo "Commit  : ${env.GIT_COMMIT}"
                sh 'git log --oneline -5'
            }
        }

        stage('Lint') {
            steps {
                sh '''
                docker run --rm \
                  --volumes-from jenkins \
                  -w $WORKSPACE \
                  python:3.12-slim \
                  sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100"
                '''
            }
        }

        stage('Build & Test') {
            steps {
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
                sh """
                docker run --rm \
                  ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                  pytest tests/ -v \
                  --cov=src \
                  --cov-report=xml:coverage.xml \
                  --cov-report=term-missing \
                  --cov-fail-under=70
                """
            }
            post {
                failure {
                    echo("Tests echoues ou coverage insuffisant")
                }
            }
        }

        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    sh "echo \$REGISTRY_PASS | docker login ghcr.io -u \$REGISTRY_USER --password-stdin"
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest"
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
                }
            }
        }
    }

    post {
        always {
            sh 'docker compose down -v 2>/dev/null || true'
        }
        success {
            echo("Pipeline reussi")
        }
        failure {
            echo("Pipeline echoue")
        }
    }
}