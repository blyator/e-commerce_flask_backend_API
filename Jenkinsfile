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

        stage('Lint') {
            steps {
                sh "python3 -m pip install -r tests/lint/requirements.txt"
                sh "python3 -m pip install black isort"
                sh "isort backend/ --check-only --diff"
                sh "black backend/ --check --diff"
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
                    echo "Rebuilding and restarting containers..."

                    sh "docker-compose -f ${DEPLOY_PATH}/${COMPOSE_FILE} --project-directory ${DEPLOY_PATH} up -d --build"
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