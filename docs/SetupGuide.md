# Setup Guide

## Prerequisites

- Docker and Docker Compose
- Kubernetes (for production setup)
- Redis for session management
- MongoDB or a relational database (MySQL/PostgreSQL) for message storage

## Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/repo.git
   cd realtime-messaging
   ```

2. **Configure environment variables**
   - Copy `config.dev.yaml` to the `configs/` directory.
   - Modify database and service URLs as needed.

3. **Start services with Docker Compose**

   ```bash
   docker-compose up
   ```

4. **Run tests**

   ```bash
   python -m unittest discover tests/
   ```

5. **Access the application**
   - API: `http://localhost:5000`
   - WebSocket: `ws://localhost:5001`

## Production Deployment

1. **Kubernetes Deployment**
   - Modify `K8sManifests.yaml` for your cloud environment.
   - Deploy services using kubectl:
  
   ```bash
   kubectl apply -f kubernetes/K8sManifests.yaml
   ```

2. **Set up Auto Scaling**
   - Configure auto-scaling using the Kubernetes Horizontal Pod Autoscaler.

3. **Configure Load Balancing**
   - Set up NGINX or HAProxy for load balancing WebSocket and HTTP traffic.
