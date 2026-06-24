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
                script { echo "Branche : ${env.GIT_BRANCH ?: 'inconnue'}" }
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    for f in $(find src/ -name "*.py"); do
                        if [ -n "$(tail -c1 "$f")" ]; then
                            echo "" >> "$f"
                        fi
                    done
                '''
                sh 'docker run --rm --volumes-from jenkins -w "$WORKSPACE" python:3.12-slim sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100"'
            }
        }

        stage('IaC Validate') {
            steps {
                dir('infra') {
                    sh 'terraform init -backend=false -input=false'
                    sh 'terraform fmt -check'
                    sh 'terraform validate'
                }
            }
        }

        stage('Build & Test') {
            steps {
                sh 'docker rm -f test-runner 2>/dev/null || true'
                sh 'docker build --no-cache -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                sh """
                    set +e
                    docker run --rm \
                    -v "${WORKSPACE}:/app/workspace" \
                    -e CI=true \
                    --memory="2g" --memory-swap="3g" \
                    --name test-runner \
                    ${IMAGE_NAME}:${IMAGE_TAG} \
                    pytest tests/ --cov=src --cov-report=xml:/app/workspace/coverage.xml --cov-fail-under=70
                    echo \$? > test_exit_code.txt
                    set -e
                """
                script {
                    if (readFile('test_exit_code.txt').trim() != '0') {
                        error "Tests échoués ou couverture < 70%."
                    }
                }
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
                    -Dsonar.sources=src \
                    -Dsonar.python.version=3.11 \
                    -Dsonar.python.coverage.reportPaths="coverage.xml" \
                    -Dsonar.scanner.metadataFilePath=\$WORKSPACE/report-task.txt
                """
            }
        }

        stage('Quality Gate') {
            environment { SONAR_AUTH_TOKEN = credentials('sonar-token') }
            steps {
                script {
                    sleep 10
                    def taskId = sh(script: "grep 'ceTaskId=' ${WORKSPACE}/report-task.txt | cut -d'=' -f2", returnStdout: true).trim()
                    def status = 'PENDING'
                    def retries = 15
                    while (retries-- > 0 && status != 'SUCCESS' && status != 'FAILED' && status != 'ERROR') {
                        sleep 5
                        def response = sh(script: "curl -sf --user \"\${SONAR_AUTH_TOKEN}:\" \"http://sonarqube:9000/api/ce/task?id=${taskId}\" || echo '{}'", returnStdout: true).trim()
                        status = sh(script: "echo '${response}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('task',{}).get('status','PENDING'))\"", returnStdout: true).trim()
                    }
                    if (status != 'SUCCESS') { error "Quality Gate SonarQube échoué : ${status}" }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    docker run --rm --volumes-from jenkins -v /var/run/docker.sock:/var/run/docker.sock \
                    -v trivy-cache:/root/.cache/trivy -w "$WORKSPACE" aquasec/trivy:latest image \
                    --severity HIGH,CRITICAL --exit-code 1 --ignorefile "$WORKSPACE/.trivyignore" \
                    --format table sentiment-ai:latest
                '''
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('IaC Apply') {
            when { branch 'main' }
            steps {
                dir('infra') {
                    sh 'terraform init -input=false'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                echo "Déploiement en cours..."
                sh '''
                    docker compose -f docker-compose.yml -p staging down 2>/dev/null || true
                    docker compose -f docker-compose.yml -p staging up -d
                '''
            }
        }
    }

    post {
        always { sh "rm -f test_exit_code.txt || true" }
        success { echo 'Pipeline terminé avec succès !' }
        failure { echo 'Le pipeline a échoué. Vérifiez les logs.' }
    }
}