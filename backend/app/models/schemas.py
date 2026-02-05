"""Pydantic models for API requests and responses"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class BaseDockerConfig(BaseModel):
    """Base configuration for all Dockerfiles"""
    language: Literal["python", "nodejs", "java"]
    framework: str
    runtime_version: str
    port: int = Field(default=8000, ge=1, le=65535)
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    health_check_path: str = "/health"
    base_image: Optional[str] = None
    user: str = "appuser"
    system_dependencies: List[str] = Field(default_factory=list)
    service_url: Optional[str] = None
    custom_start_command: Optional[str] = None


class PythonConfig(BaseDockerConfig):
    """Python-specific configuration"""
    language: Literal["python"] = "python"
    framework: Literal["fastapi", "flask", "django", "generic"] = "generic"
    package_manager: Literal["pip", "poetry"] = "pip"
    server: Optional[Literal["uvicorn", "gunicorn"]] = None
    requirements_content: Optional[str] = None
    entrypoint_file: str = "main.py"

    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "framework": "fastapi",
                "runtime_version": "3.11",
                "port": 8000,
                "package_manager": "pip",
                "server": "uvicorn",
                "requirements_content": "fastapi==0.115.0\nuvicorn[standard]==0.32.0",
                "entrypoint_file": "main.py",
                "environment_vars": {"ENV": "production"},
                "health_check_path": "/health",
                "user": "appuser",
                "system_dependencies": []
            }
        }


class NodeJSConfig(BaseDockerConfig):
    """Node.js-specific configuration"""
    language: Literal["nodejs"] = "nodejs"
    framework: Literal["express", "nestjs", "nextjs", "generic"] = "generic"
    package_manager: Literal["npm", "yarn", "pnpm"] = "npm"
    package_json: Optional[Dict] = None
    build_command: Optional[str] = None
    start_command: str = "npm start"

    class Config:
        json_schema_extra = {
            "example": {
                "language": "nodejs",
                "framework": "express",
                "runtime_version": "20",
                "port": 3000,
                "package_manager": "npm",
                "package_json": {
                    "dependencies": {
                        "express": "^4.18.0"
                    }
                },
                "start_command": "node server.js",
                "environment_vars": {"NODE_ENV": "production"},
                "health_check_path": "/health",
                "user": "appuser",
                "system_dependencies": []
            }
        }


class JavaConfig(BaseDockerConfig):
    """Java-specific configuration"""
    language: Literal["java"] = "java"
    framework: Literal["spring-boot"] = "spring-boot"
    build_tool: Literal["maven", "gradle", "jar"]
    jar_file_name: Optional[str] = None
    main_class: Optional[str] = None
    jvm_options: str = "-Xmx512m"
    build_file_content: Optional[str] = None  # pom.xml or build.gradle content

    class Config:
        json_schema_extra = {
            "example": {
                "language": "java",
                "framework": "spring-boot",
                "runtime_version": "17",
                "port": 8080,
                "build_tool": "jar",
                "jar_file_name": "app.jar",
                "jvm_options": "-Xmx512m",
                "environment_vars": {"SPRING_PROFILES_ACTIVE": "prod"},
                "health_check_path": "/actuator/health",
                "user": "appuser",
                "system_dependencies": []
            }
        }


class ProjectInfo(BaseModel):
    """Information detected from uploaded files or user input"""
    language: str
    framework: str
    detected_version: Optional[str] = None
    build_tool: Optional[str] = None
    main_class: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    """Request for generating Dockerfile"""
    project_info: Optional[ProjectInfo] = None
    config: Dict  # Will be validated based on language

    class Config:
        json_schema_extra = {
            "example": {
                "project_info": {
                    "language": "python",
                    "framework": "fastapi",
                    "detected_version": "3.11"
                },
                "config": {
                    "language": "python",
                    "framework": "fastapi",
                    "runtime_version": "3.11",
                    "port": 8000,
                    "requirements_content": "fastapi==0.115.0"
                }
            }
        }


class GenerateResponse(BaseModel):
    """Response for Dockerfile generation"""
    dockerfile: str
    session_id: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    """Response for file/config analysis"""
    project_info: ProjectInfo
    session_id: Optional[str] = None
    suggestions: Dict[str, str] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    """Response for file upload"""
    session_id: str
    filename: str
    size: int
    project_info: ProjectInfo


class JenkinsBuildRequest(BaseModel):
    """Request for Jenkins build trigger"""
    # Dockerfile configuration
    config: Dict = Field(..., description="Dockerfile generation config")

    # Jenkins settings
    jenkins_url: str = Field(..., description="Jenkins server URL (e.g., http://jenkins.example.com:8080)")
    jenkins_job: str = Field(..., description="Jenkins Pipeline job name")
    jenkins_token: str = Field(..., description="Jenkins API token")
    jenkins_username: str = Field(default="admin", description="Jenkins username")

    # Git settings
    git_url: str = Field(..., description="Git repository URL")
    git_branch: str = Field(default="main", description="Git branch to checkout")
    git_credential_id: Optional[str] = Field(None, description="Jenkins credential ID for Git (if private repo)")

    # Docker image settings
    image_name: str = Field(..., description="Docker image name")
    image_tag: str = Field(default="latest", description="Docker image tag")

    # Pipeline type
    use_kubernetes: bool = Field(default=False, description="Use Kubernetes-compatible pipeline (for Jenkins on K8s)")
    use_kaniko: bool = Field(default=False, description="Use Kaniko instead of Docker-in-Docker (no privileged mode required)")

    # Harbor Registry settings (optional)
    harbor_url: Optional[str] = Field(None, description="Harbor registry URL (e.g., harbor.example.com/project)")
    harbor_credential_id: Optional[str] = Field(None, description="Jenkins credential ID for Harbor authentication")

    class Config:
        json_schema_extra = {
            "example": {
                "config": {
                    "language": "python",
                    "framework": "generic",
                    "port": 8000,
                    "base_image": "python:3.11-slim"
                },
                "jenkins_url": "http://jenkins.example.com:8080",
                "jenkins_job": "dockerfile-builder",
                "jenkins_token": "11234567890abcdef",
                "jenkins_username": "admin",
                "git_url": "https://github.com/user/repo.git",
                "git_branch": "main",
                "git_credential_id": "github-credentials",
                "image_name": "my-app",
                "image_tag": "v1.0.0"
            }
        }


class JenkinsBuildResponse(BaseModel):
    """Response for Jenkins build trigger"""
    job_name: str = Field(..., description="Jenkins job name")
    queue_id: Optional[str] = Field(None, description="Jenkins queue item ID")
    queue_url: str = Field(..., description="Jenkins queue item URL")
    job_url: str = Field(..., description="Jenkins job URL")
    build_number: Optional[int] = Field(None, description="Jenkins build number")
    build_url: Optional[str] = Field(None, description="Jenkins build URL")
    status: str = Field(..., description="Build status (QUEUED, BUILDING, SUCCESS, FAILURE)")
    message: str = Field(default="", description="Additional message")

    class Config:
        json_schema_extra = {
            "example": {
                "job_name": "dockerfile-builder",
                "queue_id": "123",
                "queue_url": "http://jenkins.example.com:8080/queue/item/123/",
                "job_url": "http://jenkins.example.com:8080/job/dockerfile-builder/",
                "build_number": 42,
                "build_url": "http://jenkins.example.com:8080/job/dockerfile-builder/42",
                "status": "BUILDING",
                "message": "Build triggered successfully"
            }
        }
