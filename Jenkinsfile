pipeline {
    agent any

    environment {
        REGISTRY     = "localhost:9100"
        IMAGE_NAME   = "flask-site"
        PYTHON       = "./.venv/bin/python3"
        PIP          = "./.venv/bin/pip"
        COMMIT_SHORT = ""
    }

    stages {
        stage('Checkout Source') {
            steps {
                script {
                    // Calculate the hash and assign it to the environment variable
                    env.COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }
        
        stage('Set up virtual environment') {
            steps {
                sh '''#!/bin/bash
                    if [ ! -d ".venv" ]; then
                        echo "Creating virtual environment..."
                        python3 -m venv .venv
                    else
                        echo "Virtual environment already exists."
                    fi

                    echo "Installing dependencies..."
                    pwd
                    ls -al .venv/bin/
                    $PIP install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''#!/bin/bash
                    # $PYTHON -m pytest
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh '''#!/bin/bash
                    gitCommitShort=git rev-parse --short HEAD
                    $COMMIT_SHORT=$gitCommitShort
                    docker build -t $REGISTRY/$IMAGE_NAME:$gitCommitShort .
                '''
            }
        }

        stage('Push image to local registry') {
            steps {
                sh '''#!/bin/bash
                    echo $COMMIT_SHORT
                    docker push $REGISTRY/$IMAGE_NAME:$COMMIT_SHORT
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
