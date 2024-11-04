#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

# Load environment configuration (development/production)
ENV=$1
if [ -z "$ENV" ]; then
  echo "Usage: ./Deploy.sh [environment]"
  echo "Available environments: dev, prod"
  exit 1
fi

echo "Deploying the Real-Time Messaging System in $ENV environment"

# Load the respective environment configuration
CONFIG_FILE="./configs/config.$ENV.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Configuration file not found: $CONFIG_FILE"
  exit 1
fi

# Build the Docker images
echo "Building Docker images..."
docker-compose -f ./docker/DockerCompose.yml build

# Push Docker images to the container registry
echo "Pushing Docker images to registry..."
docker-compose -f ./docker/DockerCompose.yml push

# Deploy infrastructure using Terraform 
if [ "$ENV" == "prod" ]; then
  echo "Provisioning cloud infrastructure with Terraform..."
  cd ./deployment/terraform
  terraform init
  terraform apply -auto-approve
  cd ../../
fi

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f ./deployment/kubernetes/K8sManifests.yaml

# Run database migrations
echo "Running database migrations..."
./scripts/MigrateDB.sh $ENV

# Deploy services using Docker Compose 
if [ "$ENV" == "dev" ]; then
  echo "Starting services with Docker Compose..."
  docker-compose -f ./docker/DockerCompose.yml up -d
fi

# Verify deployment
echo "Verifying deployment..."
kubectl get pods
kubectl get services

echo "Deployment completed successfully in $ENV environment"