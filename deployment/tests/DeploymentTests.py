import unittest
import os
import subprocess
import yaml
import docker

class DeploymentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Executed once before all tests."""
        cls.docker_client = docker.from_env()
        cls.kubeconfig_path = os.getenv('KUBECONFIG', '~/.kube/config')
        cls.docker_compose_file = 'docker-compose.yml'
        cls.kubernetes_manifest = 'kubernetes/K8sManifests.yaml'
        cls.terraform_dir = 'terraform/'
        cls.cloudformation_template = 'cloudformation/CFTemplate.yaml'
        cls.docker_image_name = 'realtime-messaging:latest'

    def test_docker_compose_up(self):
        """Test Docker Compose services are starting correctly."""
        print("Testing Docker Compose services...")

        # Run docker-compose up in detached mode
        result = subprocess.run(
            ['docker-compose', '-f', self.docker_compose_file, 'up', '-d'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error in docker-compose up: {result.stderr.decode('utf-8')}")
        
        # Verify services are running
        containers = self.docker_client.containers.list()
        self.assertTrue(containers, "No containers are running after docker-compose up.")
        
        # Tear down docker compose
        subprocess.run(['docker-compose', '-f', self.docker_compose_file, 'down'])

    def test_docker_image_build(self):
        """Test Docker image can be built correctly."""
        print("Testing Docker image build...")

        result = subprocess.run(
            ['docker', 'build', '-t', self.docker_image_name, '.'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error building Docker image: {result.stderr.decode('utf-8')}")

        # Check if image exists locally
        image_exists = self.docker_client.images.list(name=self.docker_image_name)
        self.assertTrue(image_exists, "Docker image not found after build.")

    def test_kubernetes_deployment(self):
        """Test Kubernetes deployment using manifests."""
        print("Testing Kubernetes deployment...")

        with open(self.kubernetes_manifest, 'r') as f:
            manifest = yaml.safe_load(f)

        # Check that required fields are present in the manifest
        self.assertIn('apiVersion', manifest)
        self.assertIn('kind', manifest)
        self.assertIn('metadata', manifest)

        # Simulate kubectl apply
        result = subprocess.run(
            ['kubectl', 'apply', '-f', self.kubernetes_manifest],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error applying Kubernetes manifest: {result.stderr.decode('utf-8')}")

        # Simulate kubectl get pods
        result = subprocess.run(
            ['kubectl', 'get', 'pods'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, "Error fetching Kubernetes pods status.")

    def test_kubernetes_pod_status(self):
        """Verify that all Kubernetes pods are running."""
        print("Testing Kubernetes pod status...")

        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-o', 'json'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, "Error fetching pod status.")

        pods = yaml.safe_load(result.stdout)
        for pod in pods['items']:
            pod_phase = pod['status']['phase']
            self.assertEqual(pod_phase, 'Running', f"Pod {pod['metadata']['name']} is not running.")

    def test_terraform_plan(self):
        """Test Terraform plan for infrastructure provisioning."""
        print("Testing Terraform plan...")

        result = subprocess.run(
            ['terraform', 'plan', '-input=false', '-no-color'],
            cwd=self.terraform_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error running terraform plan: {result.stderr.decode('utf-8')}")

        # Check the output of terraform plan to ensure infrastructure changes
        output = result.stdout.decode('utf-8')
        self.assertIn('Plan:', output, "Terraform plan did not produce expected output.")

    def test_terraform_apply(self):
        """Test Terraform apply for infrastructure provisioning."""
        print("Testing Terraform apply...")

        result = subprocess.run(
            ['terraform', 'apply', '-input=false', '-auto-approve', '-no-color'],
            cwd=self.terraform_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error running terraform apply: {result.stderr.decode('utf-8')}")

        # Check that apply was successful
        output = result.stdout.decode('utf-8')
        self.assertIn('Apply complete!', output, "Terraform apply did not complete successfully.")

    def test_cloudformation_template(self):
        """Test AWS CloudFormation template validation."""
        print("Testing CloudFormation template validation...")

        result = subprocess.run(
            ['aws', 'cloudformation', 'validate-template', '--template-body', f'file://{self.cloudformation_template}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"CloudFormation template validation failed: {result.stderr.decode('utf-8')}")

    def test_ci_cd_pipeline(self):
        """Test CI/CD pipeline using GitHub Actions."""
        print("Testing CI/CD pipeline...")

        # Simulate a CI run using GitHub Actions workflow
        ci_workflow = '.github/workflows/CI.yml'
        result = subprocess.run(
            ['gh', 'workflow', 'run', ci_workflow],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, f"Error triggering GitHub Actions workflow: {result.stderr.decode('utf-8')}")

        # Fetch workflow runs to verify execution
        result = subprocess.run(
            ['gh', 'run', 'list', '--workflow', ci_workflow],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.assertEqual(result.returncode, 0, "Error fetching CI workflow runs.")

    @classmethod
    def tearDownClass(cls):
        """Executed once after all tests."""
        # Clean up resources
        subprocess.run(['docker-compose', '-f', cls.docker_compose_file, 'down'])

if __name__ == '__main__':
    unittest.main()