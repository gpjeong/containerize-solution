"""Dockerfile generation service"""
from typing import Dict, Any
import logging

from app.models.schemas import ProjectInfo, PythonConfig, NodeJSConfig, JavaConfig
from app.services.template_engine import template_engine

logger = logging.getLogger(__name__)


class DockerfileGenerator:
    """Generates optimized Dockerfiles using Jinja2 templates"""

    def __init__(self):
        self.template_engine = template_engine

    async def generate(
        self,
        project_info: ProjectInfo,
        user_config: Dict[str, Any]
    ) -> str:
        """
        Generate Dockerfile from project info and user config

        Args:
            project_info: Detected project information
            user_config: User-provided configuration

        Returns:
            str: Generated Dockerfile content
        """
        # Select appropriate template
        template_name = self._select_template(project_info, user_config)

        # Build context by merging project info and user config
        context = self._build_context(project_info, user_config)

        # Render Dockerfile
        dockerfile = await self.template_engine.render(template_name, context)

        logger.info(f"Generated Dockerfile for {project_info.language}/{project_info.framework}")
        return dockerfile

    def _select_template(self, project_info: ProjectInfo, config: Dict[str, Any]) -> str:
        """
        Select appropriate template based on language and framework

        Args:
            project_info: Project information
            config: User configuration

        Returns:
            str: Template path relative to template directory
        """
        language = project_info.language
        framework = project_info.framework

        # Map to template file
        template_map = {
            "python": {
                "fastapi": "python/fastapi.dockerfile.j2",
                "flask": "python/flask.dockerfile.j2",
                "django": "python/django.dockerfile.j2",
            },
            "nodejs": {
                "express": "nodejs/express.dockerfile.j2",
                "nestjs": "nodejs/nestjs.dockerfile.j2",
                "nextjs": "nodejs/nextjs.dockerfile.j2",
            },
            "java": {
                "spring-boot": "java/spring-boot-jar.dockerfile.j2",
            }
        }

        template_path = template_map.get(language, {}).get(framework)

        if not template_path:
            # Fallback to generic template
            template_path = f"{language}/generic.dockerfile.j2"
            logger.warning(f"No specific template found, using generic: {template_path}")

        return template_path

    def _build_context(self, project_info: ProjectInfo, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build template context from project info and config

        Applies security defaults and optimizations

        Args:
            project_info: Project information
            config: User configuration

        Returns:
            dict: Template context
        """
        # Start with user config
        context = config.copy()

        # Add project info
        context.update({
            "detected_framework": project_info.framework,
            "detected_version": project_info.detected_version,
            "build_tool": project_info.build_tool,
            "main_class": project_info.main_class,
            "dependencies": project_info.dependencies,
        })

        # Merge metadata
        context.update(project_info.metadata)

        # Apply security defaults
        if "user" not in context or not context["user"]:
            context["user"] = "appuser"

        if "health_check_path" not in context:
            context["health_check_path"] = "/health"

        # Ensure base_image has sensible default
        if not context.get("base_image"):
            context["base_image"] = self._default_base_image(
                project_info.language,
                context.get("runtime_version", "")
            )

        # Language-specific context adjustments
        if project_info.language == "python":
            context = self._adjust_python_context(context, project_info)
        elif project_info.language == "nodejs":
            context = self._adjust_nodejs_context(context, project_info)
        elif project_info.language == "java":
            context = self._adjust_java_context(context, project_info)

        return context

    def _default_base_image(self, language: str, version: str) -> str:
        """Get default base image for language and version"""
        defaults = {
            "python": f"python:{version}-slim" if version else "python:3.11-slim",
            "nodejs": f"node:{version}-alpine" if version else "node:20-alpine",
            "java": f"eclipse-temurin:{version}-jre-alpine" if version else "eclipse-temurin:17-jre-alpine"
        }
        return defaults.get(language, "alpine:latest")

    def _adjust_python_context(self, context: Dict, project_info: ProjectInfo) -> Dict:
        """Adjust context for Python projects"""
        # Set default server if not specified
        if not context.get("server"):
            context["server"] = project_info.metadata.get("server", "uvicorn")

        # Set default package manager
        if not context.get("package_manager"):
            context["package_manager"] = "pip"

        # Set default entrypoint
        if not context.get("entrypoint_file"):
            context["entrypoint_file"] = "main.py"

        return context

    def _adjust_nodejs_context(self, context: Dict, project_info: ProjectInfo) -> Dict:
        """Adjust context for Node.js projects"""
        # Set package manager from metadata
        if not context.get("package_manager"):
            context["package_manager"] = project_info.metadata.get("package_manager", "npm")

        # Set build and start commands
        if not context.get("build_command"):
            context["build_command"] = project_info.metadata.get("build_command", "")

        if not context.get("start_command"):
            context["start_command"] = project_info.metadata.get("start_command", "npm start")

        return context

    def _adjust_java_context(self, context: Dict, project_info: ProjectInfo) -> Dict:
        """Adjust context for Java projects"""
        # Set JAR filename from metadata
        if not context.get("jar_file_name"):
            context["jar_file_name"] = project_info.metadata.get("jar_filename", "app.jar")

        # Set JVM options if not specified
        if not context.get("jvm_options"):
            context["jvm_options"] = "-Xmx512m"

        return context


# Global instance
dockerfile_generator = DockerfileGenerator()
