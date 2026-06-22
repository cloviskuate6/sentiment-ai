// Jenkinsfile Pipeline CI/CD SentimentAI
pipeline {
    agent any // s'exécute sur n'importe quel agent disponible
    
    environment {
        IMAGE_NAME = 'sentiment-ai'
        // REMPLACEZ 'VOTRE_PSEUDO' par votre véritable identifiant GitHub
        REGISTRY   = 'ghcr.io/cloviskuate6' 
        
        // Extrait les 7 premiers caractères du SHA du commit actuel pour le traçage
        IMAGE_TAG  = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
    }

    stages {
        
        // Stage 1: Récupération du code
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branche : ${env.BRANCH_NAME}"
                echo "Commit  : ${env.GIT_COMMIT}"
                sh 'git log --oneline -5'
            }
        }

        // Stage 2: Analyse statique du code (Fail Fast)
        stage('Lint') {
            steps {
                // Utilise un conteneur éphémère python pour lancer flake8 sur le workspace
                sh '''
                docker run --rm \
                  --volumes-from jenkins \
                  -w $WORKSPACE \
                  python:3.12-slim \
                  sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100"
                '''
            }
        }

        // Stage 3: Construction et Tests Unitaires (Quality Gate)
        stage('Build & Test') {
            steps {
                // Construction de l'image Docker avec le tag complet du registre
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
                
                // Exécution des tests pytest et calcul de la couverture de code
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
                    // CORRECTION ICI : Ajout des parenthèses pour éviter l'erreur CPS à cause du (< 70%)
                    echo('Tests échoués ou coverage insuffisant (< 70%)')
                }
            }
        }

        // Stage 4: Publication de l'image (Uniquement sur la branche main)
        stage('Push') {
            when {
                branch 'main' // Ne s'exécute pas sur les branches de feature
            }
            steps {
                // Gestion sécurisée des identifiants GitHub enregistrés dans Jenkins
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    // Connexion sécurisée au registre GitHub Packages (ghcr.io)
                    sh "echo \$REGISTRY_PASS | docker login ghcr.io -u \$REGISTRY_USER --password-stdin"
                    
                    // Push du tag spécifique (SHA du commit)
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                    
                    // Push du tag "latest"
                    sh "docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest"
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:latest"
                }
            }
        }
    }

    post {
        always {
            // Nettoyer les conteneurs et volumes temporaires, succès ou échec
            sh 'docker compose down -v 2>/dev/null || true'
        }
        success {
            echo "Pipeline réussi ! Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline échoué. Consultez les logs ci-dessus.'
        }
    }
}