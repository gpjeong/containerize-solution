"""Template engine for rendering Dockerfiles"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import logging

from app.config import TEMPLATE_DIR

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Jinja2-based template rendering for Dockerfiles"""

    def __init__(self, template_dir: Path = TEMPLATE_DIR):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Add custom filters
        self.env.filters['split_jvm_options'] = self._split_jvm_options

    def _split_jvm_options(self, options: str) -> list:
        """Split JVM options string into list"""
        return [opt.strip() for opt in options.split() if opt.strip()]

    async def render(self, template_name: str, context: dict) -> str:
        """
        Render a template with the given context

        Args:
            template_name: Template file name (e.g., 'python/fastapi.dockerfile.j2')
            context: Template context variables

        Returns:
            str: Rendered template content
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)
            logger.info(f"Rendered template: {template_name}")
            return rendered
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def list_templates(self) -> dict:
        """
        List all available templates

        Returns:
            dict: Templates organized by language
        """
        templates = {
            "python": [],
            "nodejs": [],
            "java": []
        }

        for lang in templates.keys():
            lang_dir = self.template_dir / lang
            if lang_dir.exists():
                templates[lang] = [
                    f.stem.replace('.dockerfile', '')
                    for f in lang_dir.glob('*.dockerfile.j2')
                ]

        return templates


# Global instance
template_engine = TemplateEngine()
