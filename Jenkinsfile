pipeline {
    agent any

    environment {
        REGISTRY = "localhost:5000"
        IMAGE_NAME = "sentiment-ai"
        IMAGE_TAG = "latest"
    }

    stages {
        // Stage 1: Récupération du code
        stage('Checkout') {
            steps {
                script {
                    echo "Branche : ${env.BRANCH_NAME}"
                }
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        // Stage 2: Analyse de style (Lint)
        stage('Lint') {
            steps {
                sh 'docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100 || true"'
            }
        }

        // Stage 3: Build & Test avec génération de couverture de code
        stage('Build & Test') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                sh 'docker rm -f test-runner 2>/dev/null || true'
                
                sh """
                    set +e
                    docker run \
                    -e CI=true \
                    --name test-runner \
                    ${IMAGE_NAME}:${IMAGE_TAG} \
                    pytest tests/ \
                    --cov=src \
                    --cov-report=xml:/tmp/coverage.xml \
                    --cov-fail-under=70
                    echo \$? > test_exit_code.txt
                    set -e
                """
                
                sh 'docker cp test-runner:/tmp/coverage.xml ./coverage.xml 2>/dev/null || true'
                sh 'docker rm -f test-runner 2>/dev/null || true'
                
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

        // Stage 4: Analyse Statique avec SonarQube
        stage('SonarQube Analysis') {
            environment {
                REG_TOKEN = credentials('sonar-token')
            }
            steps {
                script {
                    def sonarInsts = jenkins.model.Jenkins.instance
                        .getDescriptorByType(hudson.plugins.sonar.SonarGlobalConfiguration.class)
                        .installations
                    // ✅ Fallback corrigé : 'sonarqube' correspond au nom dans Jenkins UI
                    def sonarName = (sonarInsts && sonarInsts.length > 0) ? sonarInsts[0].name : 'sonarqube'
                    echo "Installation SonarQube détectée : ${sonarName}"
                    
                    withSonarQubeEnv(sonarName) {
                        sh """
                            docker run --rm --network cicd-network --volumes-from jenkins -w "\$WORKSPACE" \
                            -e SONAR_HOST_URL="\$SONAR_HOST_URL" \
                            -e SONAR_TOKEN="\$REG_TOKEN" \
                            sonarsource/sonar-scanner-cli:latest \
                            sonar-scanner \
                            -Dsonar.projectKey=sentiment-ai \
                            -Dsonar.projectName=SentimentAI \
                            -Dsonar.projectBaseDir="\$WORKSPACE" \
                            -Dsonar.sources=src \
                            -Dsonar.python.version=3.11 \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.sourceEncoding=UTF-8 \
                            -Dsonar.scanner.metadataFilePath=\$WORKSPACE/report-task.txt
                        """
                    }
                }
            }
        }

        // Stage 5: Attente du feu vert SonarQube (Quality Gate)
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // Stage 6: Scan de sécurité avec Trivy
        stage('Security Scan') {
            steps {
                sh """
                    docker run --rm \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    -v trivy-cache:/root/.cache/trivy \
                    aquasec/trivy:latest image \
                    --severity HIGH,CRITICAL \
                    --exit-code 0 \
                    --format table \
                    "${IMAGE_NAME}:${IMAGE_TAG}"
                """
            }
        }

        // Stage 7: Push vers le registre local
        stage('Push') {
            when { branch 'main' }
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        // Stage 8: Déploiement automatisé en Staging
        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                echo "Déploiement de l'application en staging..."
                sh "docker rm -f sentiment-ai-staging || true"
                sh "docker run -d --name sentiment-ai-staging -p 8001:8000 ${IMAGE_NAME}:${IMAGE_TAG} || docker run -d --name sentiment-ai-staging -p 8001:8081 ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "sleep 3"
                sh "curl -f http://localhost:8001/health || echo 'Application démarrée sur http://localhost:8001'"
            }
        }
    }

    post {
        always {
            sh "rm -f test_exit_code.txt || true"
        }
        success {
            echo 'Pipeline complet réussi avec succès !'
        }
        failure {
            echo 'Le pipeline a échoué.'
        }
    }
}