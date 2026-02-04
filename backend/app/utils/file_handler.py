"""File upload and management utilities"""
from pathlib import Path
from uuid import uuid4
import aiofiles
import asyncio
import shutil
import logging
from fastapi import UploadFile

from app.config import UPLOAD_DIR, SESSION_CLEANUP_DELAY
from app.utils.security import sanitize_filename

logger = logging.getLogger(__name__)


class UploadManager:
    """Manages file uploads and session storage"""

    def __init__(self, base_path: Path = UPLOAD_DIR):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> tuple[str, Path]:
        """
        Save uploaded file to session directory

        Args:
            file: The uploaded file

        Returns:
            tuple: (session_id, file_path)
        """
        # Generate unique session ID
        session_id = str(uuid4())
        session_dir = self.base_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        file_path = session_dir / safe_filename

        # Save file in chunks (streaming for memory efficiency)
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                await f.write(chunk)

        logger.info(f"Saved upload: {safe_filename} to session {session_id}")

        # Schedule cleanup
        asyncio.create_task(self._cleanup_after_delay(session_dir, SESSION_CLEANUP_DELAY))

        return session_id, file_path

    async def _cleanup_after_delay(self, directory: Path, delay: int):
        """
        Clean up session directory after delay

        Args:
            directory: Directory to clean up
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
        try:
            if directory.exists():
                shutil.rmtree(directory)
                logger.info(f"Cleaned up session directory: {directory.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup {directory}: {e}")

    def get_session_dir(self, session_id: str) -> Path:
        """
        Get session directory path

        Args:
            session_id: Session ID

        Returns:
            Path: Session directory path
        """
        return self.base_path / session_id

    def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists

        Args:
            session_id: Session ID

        Returns:
            bool: True if session exists
        """
        return self.get_session_dir(session_id).exists()

    async def save_dockerfile(self, session_id: str, content: str) -> Path:
        """
        Save generated Dockerfile to session directory

        Args:
            session_id: Session ID
            content: Dockerfile content

        Returns:
            Path: Path to saved Dockerfile
        """
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            session_dir.mkdir(parents=True, exist_ok=True)

        dockerfile_path = session_dir / "Dockerfile"
        async with aiofiles.open(dockerfile_path, 'w') as f:
            await f.write(content)

        logger.info(f"Saved Dockerfile to session {session_id}")
        return dockerfile_path


# Global instance
upload_manager = UploadManager()
