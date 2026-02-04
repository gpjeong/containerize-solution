"""File and configuration analysis service"""
import zipfile
import json
import re
from pathlib import Path
from typing import Dict, Optional
import logging

from app.models.schemas import ProjectInfo

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """Analyzes files and configurations to detect language, framework, and build tools"""

    async def analyze_java_artifact(self, file_path: Path) -> ProjectInfo:
        """
        Analyze JAR/WAR file

        Extracts:
        - MANIFEST.MF for Spring Boot version, main class
        - Build tool detection
        - Fat JAR vs Thin JAR

        Args:
            file_path: Path to JAR/WAR file

        Returns:
            ProjectInfo: Detected project information
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as jar:
                manifest_info = self._parse_manifest(jar)

                # Detect if it's a Spring Boot application
                framework = "spring-boot" if manifest_info.get("spring_boot") else "java"

                # Detect build tool from manifest or JAR structure
                build_tool = self._detect_java_build_tool(jar, manifest_info)

                return ProjectInfo(
                    language="java",
                    framework=framework,
                    detected_version=manifest_info.get("java_version", "17"),
                    build_tool=build_tool,
                    main_class=manifest_info.get("main_class"),
                    metadata={
                        "spring_boot_version": manifest_info.get("spring_boot_version", ""),
                        "fat_jar": str(manifest_info.get("fat_jar", True)),
                        "jar_filename": file_path.name
                    }
                )

        except Exception as e:
            logger.error(f"Failed to analyze JAR file: {e}")
            raise

    def _parse_manifest(self, jar: zipfile.ZipFile) -> Dict:
        """
        Parse MANIFEST.MF from JAR file

        Args:
            jar: ZipFile object

        Returns:
            dict: Parsed manifest information
        """
        try:
            manifest_data = jar.read('META-INF/MANIFEST.MF').decode('utf-8')
            manifest = {}

            # Parse manifest entries
            for line in manifest_data.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    manifest[key.strip()] = value.strip()

            # Extract relevant information
            result = {}

            # Main class
            if 'Main-Class' in manifest:
                result['main_class'] = manifest['Main-Class']
            elif 'Start-Class' in manifest:
                result['main_class'] = manifest['Start-Class']

            # Spring Boot detection
            if 'Spring-Boot-Version' in manifest:
                result['spring_boot'] = True
                result['spring_boot_version'] = manifest['Spring-Boot-Version']
            else:
                result['spring_boot'] = False

            # Java version (if specified)
            if 'Build-Jdk' in manifest:
                result['java_version'] = manifest['Build-Jdk'].split('.')[0]

            # Fat JAR detection (Spring Boot apps are typically fat JARs)
            result['fat_jar'] = result.get('spring_boot', False) or 'BOOT-INF' in [f.filename for f in jar.filelist]

            return result

        except Exception as e:
            logger.warning(f"Failed to parse manifest: {e}")
            return {"spring_boot": False, "fat_jar": True}

    def _detect_java_build_tool(self, jar: zipfile.ZipFile, manifest_info: Dict) -> str:
        """
        Detect build tool (Maven, Gradle, or just JAR)

        Args:
            jar: ZipFile object
            manifest_info: Parsed manifest information

        Returns:
            str: Build tool name
        """
        files = jar.namelist()

        # Check for Maven
        if any('maven' in f.lower() for f in files):
            return "maven"

        # Check for Gradle
        if any('gradle' in f.lower() for f in files):
            return "gradle"

        # Default to JAR (pre-built artifact)
        return "jar"

    async def analyze_python_config(self, requirements_content: Optional[str], framework: str) -> ProjectInfo:
        """
        Analyze Python configuration

        Args:
            requirements_content: Content of requirements.txt
            framework: User-specified framework

        Returns:
            ProjectInfo: Detected project information
        """
        dependencies = []
        detected_framework = framework
        server = None

        if requirements_content:
            # Parse requirements.txt
            for line in requirements_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before ==, >=, etc.)
                    pkg_name = re.split(r'[=<>!]', line)[0].strip()
                    dependencies.append(pkg_name)

            # Auto-detect framework if not specified
            if not framework or framework == "auto":
                if "fastapi" in dependencies:
                    detected_framework = "fastapi"
                    server = "uvicorn"
                elif "flask" in dependencies:
                    detected_framework = "flask"
                    server = "gunicorn"
                elif "django" in dependencies:
                    detected_framework = "django"
                    server = "gunicorn"

            # Detect server
            if not server:
                if detected_framework == "fastapi":
                    server = "uvicorn"
                elif detected_framework in ["flask", "django"]:
                    server = "gunicorn"

        return ProjectInfo(
            language="python",
            framework=detected_framework,
            dependencies=dependencies,
            metadata={
                "server": server or "uvicorn",
                "package_count": str(len(dependencies))
            }
        )

    async def analyze_nodejs_config(self, package_json: Optional[Dict], framework: str) -> ProjectInfo:
        """
        Analyze Node.js configuration

        Args:
            package_json: Parsed package.json content
            framework: User-specified framework

        Returns:
            ProjectInfo: Detected project information
        """
        dependencies = []
        detected_framework = framework
        package_manager = "npm"
        build_command = None
        start_command = "npm start"

        if package_json:
            # Extract dependencies
            deps = package_json.get("dependencies", {})
            dev_deps = package_json.get("devDependencies", {})
            dependencies = list(deps.keys()) + list(dev_deps.keys())

            # Auto-detect framework
            if not framework or framework == "auto":
                if "next" in deps or "next" in dev_deps:
                    detected_framework = "nextjs"
                    build_command = "npm run build"
                    start_command = "npm start"
                elif "@nestjs/core" in deps:
                    detected_framework = "nestjs"
                    build_command = "npm run build"
                    start_command = "npm run start:prod"
                elif "express" in deps:
                    detected_framework = "express"
                    start_command = "node server.js"

            # Detect package manager
            if "packageManager" in package_json:
                pm = package_json["packageManager"]
                if "yarn" in pm:
                    package_manager = "yarn"
                elif "pnpm" in pm:
                    package_manager = "pnpm"

            # Extract scripts
            scripts = package_json.get("scripts", {})
            if "build" in scripts and not build_command:
                build_command = f"{package_manager} run build"
            if "start" in scripts:
                start_command = f"{package_manager} start"

        return ProjectInfo(
            language="nodejs",
            framework=detected_framework,
            dependencies=dependencies,
            metadata={
                "package_manager": package_manager,
                "build_command": build_command or "",
                "start_command": start_command,
                "dependency_count": str(len(dependencies))
            }
        )


# Global instance
file_analyzer = FileAnalyzer()
