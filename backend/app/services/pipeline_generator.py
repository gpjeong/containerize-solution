"""Jenkins Pipeline script generator"""
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class PipelineGenerator:
    """Generates Jenkins Pipeline (Groovy) scripts for Docker builds"""

    def generate_k8s_kaniko_pipeline_script(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str,
        registry_url: Optional[str] = None,
        registry_credential_id: Optional[str] = None
    ) -> str:
        """
        Generate Kubernetes-compatible Pipeline using Kaniko (no privileged mode required)

        Kaniko builds container images without Docker daemon, making it more suitable
        for Kubernetes environments without privileged containers

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag
            registry_url: Optional registry URL for pushing

        Returns:
            str: Kubernetes-compatible Groovy pipeline script using Kaniko
        """
        # Escape special characters in Dockerfile for Groovy string
        escaped_dockerfile = dockerfile_content.replace('\\', '\\\\').replace('$', '\\$').replace('"', '\\"')

        # Build git checkout command
        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}',
                        credentialsId: '{git_credential_id}'"""
        else:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}'"""

        # Build Kaniko execution script
        if registry_url:
            # Push to Harbor with Jenkins credentials
            if registry_credential_id:
                build_script = f"""def destination = params.REGISTRY_URL + "/" + params.IMAGE_NAME + ":" + params.IMAGE_TAG
                        echo "Destination: ${{destination}}"
                        def cacheRepo = params.REGISTRY_URL + "/cache"

                        withCredentials([usernamePassword(credentialsId: '{registry_credential_id}', usernameVariable: 'HARBOR_USER', passwordVariable: 'HARBOR_PASS')]) {{
                            sh \"\"\"
                                mkdir -p /kaniko/.docker
                                cat > /kaniko/.docker/config.json << EOF
{{"auths":{{"${{params.REGISTRY_URL}}":{{"username":"${{HARBOR_USER}}","password":"${{HARBOR_PASS}}"}}}}}}
EOF
                                /kaniko/executor --context=\\$(pwd) --dockerfile=Dockerfile --destination=$destination --cache=true --cache-repo=$cacheRepo --skip-tls-verify
                            \"\"\"
                        }}"""
            else:
                # No credential - try without auth
                build_script = r"""def destination = params.REGISTRY_URL + "/" + params.IMAGE_NAME + ":" + params.IMAGE_TAG
                        echo "Destination: ${destination}"
                        def cacheRepo = params.REGISTRY_URL + "/cache"
                        sh "/kaniko/executor --context=\$(pwd) --dockerfile=Dockerfile --destination=${destination} --cache=true --cache-repo=${cacheRepo} --skip-tls-verify" """
            success_message = "Image built and pushed to Harbor successfully!"
        else:
            # Local build only
            build_script = r"""def destination = params.IMAGE_NAME + ":" + params.IMAGE_TAG
                        echo "Destination: ${destination}"
                        sh "/kaniko/executor --context=\$(pwd) --dockerfile=Dockerfile --no-push --destination=${destination} --tar-path=image.tar" """
            success_message = "Image built successfully and saved as image.tar"

        # Build Pod YAML (simple, no secret mount - will use Jenkins credentials)
        pod_yaml = """apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - /busybox/cat
    tty: true"""

        pipeline_script = f"""pipeline {{
    agent {{
        kubernetes {{
            yaml '''
{pod_yaml}
'''
        }}
    }}

    parameters {{
        string(name: 'IMAGE_NAME', defaultValue: '{image_name}', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: '{image_tag}', description: 'Docker image tag')
        {f"string(name: 'REGISTRY_URL', defaultValue: '{registry_url}', description: 'Harbor registry URL')" if registry_url else ""}
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                container('kaniko') {{
                    echo 'Cloning repository from {git_url}...'
                    {git_checkout}
                }}
            }}
        }}

        stage('Create Dockerfile') {{
            steps {{
                container('kaniko') {{
                    echo 'Creating Dockerfile from generated content...'
                    script {{
                        // Dockerfile content (plain text)
                        def dockerfileContent = \"\"\"\\
{escaped_dockerfile}\\
\"\"\"
                        writeFile file: 'Dockerfile', text: dockerfileContent
                        echo 'Dockerfile created successfully'
                        sh 'cat Dockerfile'
                    }}
                }}
            }}
        }}

        stage('Build Docker Image with Kaniko') {{
            steps {{
                container('kaniko') {{
                    echo "Building Docker image with Kaniko: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
                    script {{
                        {build_script}
                    }}
                    echo '{success_message}'
                }}
            }}
        }}

        {'' if registry_url else "stage('Verify Image') {"}
            {'' if registry_url else "steps {"}
                {'' if registry_url else "container('kaniko') {"}
                    {'' if registry_url else "echo 'Verifying built image tarball...'"}
                    {'' if registry_url else "sh 'ls -lh image.tar'"}
                {'' if registry_url else "}"}
            {'' if registry_url else "}"}
        {'' if registry_url else "}"}
    }}

    post {{
        success {{
            echo '{'Docker image built and pushed to Harbor successfully!' if registry_url else 'Docker image built successfully with Kaniko!'}'
            echo "Image: {f'${{params.REGISTRY_URL}}/' if registry_url else ''}${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
            {'' if registry_url else "echo 'Image saved as: image.tar'"}
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

        logger.info(f"Generated Kaniko pipeline script for image: {image_name}:{image_tag}")
        return pipeline_script

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

    def generate_k8s_pipeline_script_for_preview(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str
    ) -> str:
        """
        Generate Kubernetes-compatible Jenkins Pipeline script for preview

        Uses podTemplate with Docker-in-Docker (DinD) container for building images
        in Kubernetes environment

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git (optional for public repos)
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag

        Returns:
            str: Kubernetes-compatible Groovy pipeline script with readable Dockerfile
        """
        # Escape special characters in Dockerfile for Groovy string
        escaped_dockerfile = dockerfile_content.replace('\\', '\\\\').replace('$', '\\$').replace('"', '\\"')

        # Build git checkout command
        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}',
                        credentialsId: '{git_credential_id}'"""
        else:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}'"""

        pipeline_script = f"""pipeline {{
    agent {{
        kubernetes {{
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    - name: DOCKER_HOST
      value: "unix:///var/run/docker.sock"
  - name: docker-client
    image: docker:24-cli
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run
    env:
    - name: DOCKER_HOST
      value: "unix:///var/run/docker.sock"
  volumes:
  - name: docker-sock
    emptyDir: {{}}
'''
        }}
    }}

    parameters {{
        string(name: 'IMAGE_NAME', defaultValue: '{image_name}', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: '{image_tag}', description: 'Docker image tag')
    }}

    stages {{
        stage('Wait for Docker') {{
            steps {{
                container('docker-client') {{
                    echo 'Waiting for Docker daemon to be ready...'
                    sh '''
                        for i in $(seq 1 30); do
                            if docker info >/dev/null 2>&1; then
                                echo "Docker daemon is ready"
                                exit 0
                            fi
                            echo "Waiting for Docker daemon... ($i/30)"
                            sleep 2
                        done
                        echo "ERROR: Docker daemon failed to start"
                        exit 1
                    '''
                }}
            }}
        }}

        stage('Checkout') {{
            steps {{
                container('docker-client') {{
                    echo 'Cloning repository from {git_url}...'
                    {git_checkout}
                }}
            }}
        }}

        stage('Create Dockerfile') {{
            steps {{
                container('docker-client') {{
                    echo 'Creating Dockerfile from generated content...'
                    script {{
                        // Dockerfile content (plain text for readability)
                        def dockerfileContent = \"\"\"\\
{escaped_dockerfile}\\
\"\"\"
                        writeFile file: 'Dockerfile', text: dockerfileContent
                        echo 'Dockerfile created successfully'
                        sh 'cat Dockerfile'
                    }}
                }}
            }}
        }}

        stage('Build Docker Image') {{
            steps {{
                container('docker-client') {{
                    echo "Building Docker image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
                    sh \"\"\"
                        docker build -t \\${{IMAGE_NAME}}:\\${{IMAGE_TAG}} .
                    \"\"\"
                }}
            }}
        }}

        stage('Verify Image') {{
            steps {{
                container('docker-client') {{
                    echo 'Verifying Docker image...'
                    sh 'docker images | grep \\$IMAGE_NAME || echo "Image built successfully"'
                }}
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

        logger.info(f"Generated Kubernetes pipeline script for image: {image_name}:{image_tag}")
        return pipeline_script

    def generate_pipeline_script_for_preview(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str
    ) -> str:
        """
        Generate Jenkins Pipeline script for preview (with readable Dockerfile content)

        Same as generate_pipeline_script but embeds Dockerfile as plain text
        with proper escaping for better readability in preview

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git (optional for public repos)
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag

        Returns:
            str: Complete Groovy pipeline script with readable Dockerfile
        """
        # Escape special characters in Dockerfile for Groovy string
        escaped_dockerfile = dockerfile_content.replace('\\', '\\\\').replace('$', '\\$').replace('"', '\\"')

        # Build git checkout command
        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}',
                    credentialsId: '{git_credential_id}'"""
        else:
            # Public repository (no credentials)
            git_checkout = f"""git url: '{git_url}',
                    branch: '{git_branch}'"""

        # Generate pipeline script with plain Dockerfile content
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
                    // Dockerfile content (plain text for readability)
                    def dockerfileContent = \"\"\"\\
{escaped_dockerfile}\\
\"\"\"
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
                sh 'docker images | grep \\$IMAGE_NAME || echo "Image built successfully"'
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

        logger.info(f"Generated preview pipeline script for image: {image_name}:{image_tag}")
        return pipeline_script

    def generate_k8s_pipeline_script(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str
    ) -> str:
        """
        Generate Kubernetes-compatible Jenkins Pipeline script with Base64 Dockerfile

        Uses podTemplate with Docker-in-Docker (DinD) for Kubernetes environment

        Args:
            git_url: Git repository URL
            git_branch: Git branch name
            git_credential_id: Jenkins credential ID for Git (optional for public repos)
            dockerfile_content: Generated Dockerfile content
            image_name: Docker image name
            image_tag: Docker image tag

        Returns:
            str: Kubernetes-compatible Groovy pipeline script
        """
        # Encode Dockerfile content as Base64 for safe embedding
        base64_dockerfile = self.encode_dockerfile_base64(dockerfile_content)

        # Build git checkout command
        if git_credential_id:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}',
                        credentialsId: '{git_credential_id}'"""
        else:
            git_checkout = f"""git url: '{git_url}',
                        branch: '{git_branch}'"""

        pipeline_script = f"""pipeline {{
    agent {{
        kubernetes {{
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    - name: DOCKER_HOST
      value: "unix:///var/run/docker.sock"
  - name: docker-client
    image: docker:24-cli
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run
    env:
    - name: DOCKER_HOST
      value: "unix:///var/run/docker.sock"
  volumes:
  - name: docker-sock
    emptyDir: {{}}
'''
        }}
    }}

    parameters {{
        string(name: 'IMAGE_NAME', defaultValue: '{image_name}', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: '{image_tag}', description: 'Docker image tag')
    }}

    stages {{
        stage('Wait for Docker') {{
            steps {{
                container('docker-client') {{
                    echo 'Waiting for Docker daemon to be ready...'
                    sh '''
                        for i in $(seq 1 30); do
                            if docker info >/dev/null 2>&1; then
                                echo "Docker daemon is ready"
                                exit 0
                            fi
                            echo "Waiting for Docker daemon... ($i/30)"
                            sleep 2
                        done
                        echo "ERROR: Docker daemon failed to start"
                        exit 1
                    '''
                }}
            }}
        }}

        stage('Checkout') {{
            steps {{
                container('docker-client') {{
                    echo 'Cloning repository from {git_url}...'
                    {git_checkout}
                }}
            }}
        }}

        stage('Create Dockerfile') {{
            steps {{
                container('docker-client') {{
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
        }}

        stage('Build Docker Image') {{
            steps {{
                container('docker-client') {{
                    echo "Building Docker image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
                    sh \"\"\"
                        docker build -t \\${{IMAGE_NAME}}:\\${{IMAGE_TAG}} .
                    \"\"\"
                }}
            }}
        }}

        stage('Verify Image') {{
            steps {{
                container('docker-client') {{
                    echo 'Verifying Docker image...'
                    sh 'docker images | grep \\$IMAGE_NAME || echo "Image built successfully"'
                }}
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

        logger.info(f"Generated Kubernetes pipeline script for image: {image_name}:{image_tag}")
        return pipeline_script

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
                sh 'docker images | grep \\$IMAGE_NAME || echo "Image built successfully"'
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
            echo 'Docker image built and pushed successfully!'
            echo "Image: ${{params.IMAGE_NAME}}:${{params.IMAGE_TAG}}"
            echo "Registry: {registry_url}"
        }}
        failure {{
            echo 'Build failed!'
        }}
    }}
}}"""

        logger.info(f"Generated pipeline script with registry push for: {image_name}:{image_tag}")
        return pipeline_script

    def generate_k8s_kaniko_pipeline_script_for_preview(
        self,
        git_url: str,
        git_branch: str,
        git_credential_id: Optional[str],
        dockerfile_content: str,
        image_name: str,
        image_tag: str,
        registry_url: Optional[str] = None,
        registry_credential_id: Optional[str] = None
    ) -> str:
        """
        Generate Kaniko pipeline for preview (alias to standard Kaniko pipeline)

        Kaniko already uses plain text Dockerfile, so this is identical to the standard method.
        This method exists for consistency with the API naming convention.
        """
        return self.generate_k8s_kaniko_pipeline_script(
            git_url=git_url,
            git_branch=git_branch,
            git_credential_id=git_credential_id,
            dockerfile_content=dockerfile_content,
            image_name=image_name,
            image_tag=image_tag,
            registry_url=registry_url,
            registry_credential_id=registry_credential_id
        )


# Global instance
pipeline_generator = PipelineGenerator()
