pipeline {
    agent any

    environment {
        REGISTRY   = "localhost:9100"
        IMAGE_NAME = "flask-site"
        TAG        = "latest"
        PYTHON     = "./.venv/bin/python3"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: '${env.BRANCH_NAME}', url: '${env.GIT_URL}'
            }
        }

        stage('Set up virtual environment') {
            steps {
                sh '''
                    if [ ! -d ".venv" ]; then
                        echo "Creating virtual environment..."
                        python3 -m venv .venv
                    else
                        echo "Virtual environment already exists."
                    fi

                    echo "Installing dependencies..."
                    $PYTHON -m pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    $PYTHON -m pytest
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh '''
                    docker build -t $REGISTRY/$IMAGE_NAME:$TAG .
                '''
            }
        }

        stage('Push image to local registry') {
            steps {
                sh '''
                    docker push $REGISTRY/$IMAGE_NAME:$TAG
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Build and push successful! Image: $REGISTRY/$IMAGE_NAME:$TAG"
        }
        failure {
            echo "❌ Build failed. Check logs."
        }
    }
}
