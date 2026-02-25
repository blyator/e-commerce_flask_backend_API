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
                    docker compose -f ${COMPOSE_TEST} run --name sut_container sut
                '''
            }
            post {
                always {
                    script {
                        try {
                            sh "docker cp sut_container:/app/test-results.xml backend/test-results.xml"
                            junit 'backend/test-results.xml'
                        } catch (e) {
                            echo "Could not copy test results: ${e.message}"
                        }
                    }
                    // Cleanup
                    sh "docker rm -f sut_container || true"
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
