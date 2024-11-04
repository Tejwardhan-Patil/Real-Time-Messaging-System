#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting build process for Real-Time Messaging System..."

# Function to build Java components
build_java() {
  echo "Building Java components..."
  mvn clean install -f ./broker/pom.xml
  mvn clean install -f ./sessions/pom.xml
  mvn clean install -f ./notifications/pom.xml
  mvn clean install -f ./monitoring/pom.xml
}

# Function to build Python components
build_python() {
  echo "Building Python components..."
  pip install -r ./broker/requirements.txt
  pip install -r ./sessions/requirements.txt
  pip install -r ./storage/requirements.txt
  pip install -r ./notifications/requirements.txt
  pip install -r ./security/requirements.txt
  pip install -r ./api/requirements.txt
}

# Function to build Scala components
build_scala() {
  echo "Building Scala components..."
  sbt compile ./broker
  sbt compile ./sessions
  sbt compile ./storage
  sbt compile ./notifications
}

# Function to build Go components
build_go() {
  echo "Building Go components..."
  cd ./broker
  go build -o broker
  cd ../sessions
  go build -o sessions
  cd ../notifications
  go build -o notifications
  cd ../monitoring
  go build -o monitoring
}

# Function to build Docker images
build_docker() {
  echo "Building Docker images..."
  docker build -t messaging-system-broker ./broker
  docker build -t messaging-system-sessions ./sessions
  docker build -t messaging-system-storage ./storage
  docker build -t messaging-system-notifications ./notifications
  docker build -t messaging-system-api ./api
}

# Clean previous builds
clean_build() {
  echo "Cleaning previous builds..."
  mvn clean
  sbt clean
  find . -type d -name "__pycache__" -exec rm -r {} +
}

# Main build process
clean_build
build_java
build_python
build_scala
build_go
build_docker

echo "Build process completed successfully."