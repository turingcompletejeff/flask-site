pipeline {
    agent any

    environment {
        REGISTRY   = "localhost:9100"
        IMAGE_NAME = "flask-site"
        PYTHON     = "./.venv/bin/python3"
        PIP        = "./.venv/bin/pip"
    }

    stages {
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
                    $PIP install --no-cache-dir -r requirements.txt
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
                    gitShortHash=$(git rev-parse --short HEAD)
                    
                    docker build -t $REGISTRY/$IMAGE_NAME:$gitShortHash .
                '''
            }
        }

        stage('Push image to local registry') {
            steps {
                sh '''
                    gitShortHash=$(git rev-parse --short HEAD)
                    
                    docker push $REGISTRY/$IMAGE_NAME:$gitShortHash
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
