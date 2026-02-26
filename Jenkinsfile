pipeline {
    agent any

    environment {
        DEPLOY_PATH    = "/var/www/flask-ecommerce-API"
        COMPOSE_TEST   = "docker-compose.test.yml"
        COMPOSE_PROD   = "docker-compose.yml"
        TEST_CONTAINER = "test-container"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build & Lint') {
            environment { COMPOSE_PROJECT_NAME = "flask-ecommerce-api-test" }
            steps {
                sh '''
                    docker compose -f ${COMPOSE_TEST} build sut
                    docker compose -f ${COMPOSE_TEST} up -d test-db test-redis
                    docker compose -f ${COMPOSE_TEST} run -T --rm sut \
                        sh -c "isort . --check-only --diff && black . --check --diff"
                '''
            }
        }

        stage('Test') {
            environment { COMPOSE_PROJECT_NAME = "flask-ecommerce-api-test" }
            steps {
                sh '''
                    docker compose -f ${COMPOSE_TEST} run -T --name ${TEST_CONTAINER} sut
                '''
            }
            post {
                always {
                    script {
                        try {
                            sh "docker cp ${TEST_CONTAINER}:/app/test-results.xml ./backend/test-results.xml"
                            junit 'backend/test-results.xml'
                        } catch (e) {
                            echo "Could not collect test results: ${e.message}"
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Syncing workspace to ${DEPLOY_PATH}..."
                sh "rsync -rlptvz --exclude '.git' --exclude 'tests' ${WORKSPACE}/ ${DEPLOY_PATH}/"
                echo "Rebuilding and restarting production containers..."
                sh "docker rm -f shop_api shop_redis shop_db celery celery_flower shop_locust || true"
                sh "docker compose -f ${DEPLOY_PATH}/${COMPOSE_PROD} --project-directory ${DEPLOY_PATH} up -d --build"
            }
        }

        stage('Cleanup') {
            steps {
                sh "docker image prune -f"
            }
        }
    }

    post {
        always {
            echo "Final cleanup — removing test containers and volumes..."
            sh '''
                docker rm -f ${TEST_CONTAINER} || true
                COMPOSE_PROJECT_NAME=flask-ecommerce-api-test docker compose -f ${COMPOSE_TEST} down -v || true
            '''
        }
        success {
            echo "Pipeline completed successfully."
        }
        failure {
            echo "Pipeline FAILED — review logs above."
        }
    }
}