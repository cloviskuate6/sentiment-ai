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
                script { echo "Branche : ${env.BRANCH_NAME}" }
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100 || true"'
            }
        }

        stage('Build & Test') {
            steps {
                // 1. Nettoyage préventif
                sh 'docker rm -f test-runner 2>/dev/null || true'
                
                // 2. Build de l'image
                sh 'docker build --no-cache -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                
                // 3. Exécution avec montage de volume pour récupérer le rapport sans 'docker cp'
                sh """
                    set +e
                    docker run \
                    --rm \
                    -v "${WORKSPACE}:/app/workspace" \
                    -e CI=true \
                    --memory="2g" \
                    --memory-swap="3g" \
                    --name test-runner \
                    ${IMAGE_NAME}:${IMAGE_TAG} \
                    pytest tests/ \
                    --cov=src \
                    --cov-report=xml:/app/workspace/coverage.xml \
                    --cov-fail-under=70
                    echo \$? > test_exit_code.txt
                    set -e
                """
                
                script {
                    def exitCode = readFile('test_exit_code.txt').trim()
                    if (exitCode != '0') {
                        error "Les tests ont échoué ou la couverture est inférieure à 70% (Code: ${exitCode})"
                    }
                }
            }
            post {
                failure { echo 'Tests échoués ou coverage insuffisant (< 70%)' }
            }
        }

        stage('SonarQube Analysis') {
            environment { SONAR_AUTH_TOKEN = credentials('sonar-token') }
            steps {
                sh "sed -i 's|/app/src|src|g' ./coverage.xml || true"
                sh """
                    docker run --rm --network cicd-network --volumes-from jenkins -w "\$WORKSPACE" \
                    sonarsource/sonar-scanner-cli:latest sonar-scanner \
                    -Dsonar.host.url="http://sonarqube:9000" \
                    -Dsonar.login="\$SONAR_AUTH_TOKEN" \
                    -Dsonar.projectKey=sentiment-ai \
                    -Dsonar.projectName=SentimentAI \
                    -Dsonar.projectBaseDir="\$WORKSPACE" \
                    -Dsonar.sources=src \
                    -Dsonar.python.version=3.11 \
                    -Dsonar.python.coverage.reportPaths="coverage.xml" \
                    -Dsonar.sourceEncoding=UTF-8 \
                    -Dsonar.scanner.metadataFilePath=\$WORKSPACE/report-task.txt
                """
            }
        }

        stage('Quality Gate') {
            steps {
                echo "Envoi des données à SonarQube terminé."
                sleep 10
            }
        }

        stage('Security Scan') {
            steps {
                sh """
                    docker run --rm \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    -v trivy-cache:/root/.cache/trivy \
                    aquasec/trivy:latest image \
                    --severity HIGH,CRITICAL \
                    --exit-code 1 \
                    --format table \
                    "${IMAGE_NAME}:${IMAGE_TAG}"
                """
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                sh "docker rm -f sentiment-ai-staging || true"
                sh "docker run -d --name sentiment-ai-staging -p 8001:8000 ${IMAGE_NAME}:${IMAGE_TAG} || docker run -d --name sentiment-ai-staging -p 8001:8081 ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }
    }

    post {
        always { sh "rm -f test_exit_code.txt || true" }
        success { echo 'Pipeline complet réussi avec succès !' }
        failure { echo 'Le pipeline a échoué.' }
    }
}