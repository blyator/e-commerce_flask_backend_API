pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/var/www/flask-ecommerce-API"
        COMPOSE_FILE = "docker-compose.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Sync to /var/www') {
            steps {
                echo "Syncing workspace to ${DEPLOY_PATH}..."

                sh "rsync -rlptvz --exclude '.git' ${WORKSPACE}/ ${DEPLOY_PATH}/"
            }
        }

        stage('Build & Deploy') {
            steps {
                script {
                    dir("${DEPLOY_PATH}") {
                        echo "Rebuilding and restarting containers..."

                        sh "docker compose -f ${COMPOSE_FILE} up -d --build"
                    }
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh "docker image prune -f"
            }
        }
    }
}