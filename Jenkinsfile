pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/var/www/flask-ecommerce-API"
        COMPOSE_TEST = "docker-compose.test.yml"
        COMPOSE_PROD = "docker-compose.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    docker compose -f ${COMPOSE_TEST} build sut
                    docker compose -f ${COMPOSE_TEST} run --rm sut sh -c "
                        isort . --check-only --diff && \
                        black . --check --diff
                    "
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    # Run tests 
                    docker compose -f ${COMPOSE_TEST} run --rm sut
                '''
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                    // Cleanup test containers but keep images for cache
                    sh "docker compose -f ${COMPOSE_TEST} down"
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Syncing workspace to ${DEPLOY_PATH}..."
                sh "rsync -rlptvz --exclude '.git' --exclude 'tests' ${WORKSPACE}/ ${DEPLOY_PATH}/"
                
                script {
                    echo "Rebuilding and restarting production containers..."
                    sh "docker-compose -f ${DEPLOY_PATH}/${COMPOSE_PROD} --project-directory ${DEPLOY_PATH} up -d --build"
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
