"""Jenkins Pipeline script generator"""
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class PipelineGenerator:
    """Generates Jenkins Pipeline (Groovy) scripts for Docker builds"""

    @staticmethod
    def encode_dockerfile_base64(content: str) -> str:
        """
        Encode Dockerfile content as Base64 to safely embed in Groovy script

        Args:
            content: Dockerfile content

        Returns:
            str: Base64 encoded string
        """
        content_bytes = content.encode('utf-8')
        base64_bytes = base64.b64encode(content_bytes)
        base64_string = base64_bytes.decode('utf-8')
        return base64_string

    def generate_pipeline_script(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str
    ) -> str:
        """
        Generate Jenkins Pipeline script (Jenkinsfile)

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git (optional for public repos)
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag

        Returns:
            str: Complete Groovy pipeline script
        """
        # Encode Dockerfile content as Base64 for safe embedding
        base64_dockerfile = self.encode_dockerfile_base64(dockerfile_content)

        # Build git checkout command
        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}',
                    credentialsId: '{git_credential_id}'"""
        else:
            # Public repository (no credentials)
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}'"""

        # Generate pipeline script
        pipeline_script = f"""pipeline {{
    agent any

    parameters {{
        string(name: 'IMAGE_NAME', defaultValue: '{image_name}', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: '{image_tag}', description: 'Docker image tag')
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                echo 'Cloning repository from {git_url}...'
                {git_checkout}
            }}
        }}

        stage('Create Dockerfile') {{
            steps {{
                echo 'Creating Dockerfile from generated content...'
                script {{
                    // Decode Base64 Dockerfile content
                    def dockerfileBase64 = '{base64_dockerfile}'
                    def dockerfileContent = new String(dockerfileBase64.decodeBase64())
                    writeFile file: 'Dockerfile', text: dockerfileContent
                    echo 'Dockerfile created successfully'
                    sh 'cat Dockerfile'
                }}
            }}
        }}

        stage('Build Docker Image') {{
            steps {{
                echo "Building Docker image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
                script {{
                    docker.build("${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}")
                }}
            }}
        }}

        stage('Verify Image') {{
            steps {{
                echo 'Verifying Docker image...'
                sh 'docker images | grep ${{params.IMAGE_NAME}}'
            }}
        }}
    }}

    post {{
        success {{
            echo 'Docker image built successfully!'
            echo "Image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
        }}
        failure {{
            echo 'Build failed!'
            echo 'Check the console output for details'
        }}
        always {{
            echo 'Build completed'
        }}
    }}
}}"""

        logger.info(f"Generated pipeline script for image: {image_name}:{image_tag}")
        return pipeline_script

    def generate_pipeline_with_registry_push(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str,
        registry_url: str,
        registry_credential_id: str
    ) -> str:
        """
        Generate Pipeline script with Docker Registry push

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag
            registry_url: Docker registry URL
            registry_credential_id: Jenkins credential ID for registry

        Returns:
            str: Complete Groovy pipeline script with registry push
        """
        base64_dockerfile = self.encode_dockerfile_base64(dockerfile_content)

        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}',
                    credentialsId: '{git_credential_id}'"""
        else:
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}'"""

        pipeline_script = f"""pipeline {{
    agent any

    parameters {{
        string(name: 'IMAGE_NAME', defaultValue: '{image_name}', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: '{image_tag}', description: 'Docker image tag')
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                echo 'Cloning repository from {git_url}...'
                {git_checkout}
            }}
        }}

        stage('Create Dockerfile') {{
            steps {{
                echo 'Creating Dockerfile from generated content...'
                script {{
                    // Decode Base64 Dockerfile content
                    def dockerfileBase64 = '{base64_dockerfile}'
                    def dockerfileContent = new String(dockerfileBase64.decodeBase64())
                    writeFile file: 'Dockerfile', text: dockerfileContent
                    echo 'Dockerfile created successfully'
                }}
            }}
        }}

        stage('Build Docker Image') {{
            steps {{
                echo "Building Docker image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
                script {{
                    docker.build("${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}")
                }}
            }}
        }}

        stage('Push to Registry') {{
            steps {{
                echo 'Pushing image to Docker registry...'
                script {{
                    docker.withRegistry('{registry_url}', '{registry_credential_id}') {{
                        docker.image("${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}").push()
                        docker.image("${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}").push('latest')
                    }}
                }}
            }}
        }}
    }}

    post {{
        success {{
            echo '✅ Docker image built and pushed successfully!'
            echo "Image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
            echo "Registry: {registry_url}"
        }}
        failure {{
            echo '❌ Build failed!'
        }}
    }}
}}"""

        logger.info(f"Generated pipeline script with registry push for: {image_name}:{image_tag}")
        return pipeline_script


# Global instance
pipeline_generator = PipelineGenerator()
