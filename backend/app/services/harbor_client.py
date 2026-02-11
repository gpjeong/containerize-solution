import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class HarborClient:
    """Harbor Registry REST API Client"""

    def __init__(
        self,
        harbor_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False
    ):
        """
        Initialize Harbor client

        Args:
            harbor_url: Harbor base URL (e.g., https://harbor.example.com)
            username: Harbor admin username
            password: Harbor admin password
            verify_ssl: Verify SSL certificate (default: False for self-signed)
        """
        # Remove trailing slash and /api/v2.0 if present
        self.base_url = harbor_url.rstrip('/').replace('/api/v2.0', '')
        self.api_base = f"{self.base_url}/api/v2.0"
        self.auth = HTTPBasicAuth(username, password)
        self.verify_ssl = verify_ssl

        # DON'T use Session() - Harbor's CSRF protection is triggered by cookies
        # Using direct requests without session avoids CSRF token requirement
        logger.info(f"Initialized Harbor client for {self.base_url} (cookieless mode)")

    def _make_request(self, method, url, **kwargs):
        """
        Make HTTP request without cookies to bypass CSRF protection
        """
        kwargs['auth'] = self.auth
        kwargs['verify'] = self.verify_ssl
        kwargs.setdefault('timeout', 10)
        return requests.request(method, url, **kwargs)

    def _get_csrf_token_old(self):
        """
        Get CSRF token from Harbor for POST/PUT/DELETE requests
        Harbor v2.2+ requires CSRF token for state-changing operations

        For API clients using Basic Auth, Harbor provides CSRF token via:
        1. Login to get session cookie
        2. Extract CSRF token from cookie/header
        """
        try:
            # For Harbor v2.x with CSRF protection, we need to:
            # 1. Make any GET request to establish session
            # 2. Extract sid cookie which contains CSRF token

            url = f"{self.api_base}/systeminfo"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                # Harbor v2.x uses '_gorilla_csrf' cookie as CSRF token
                # Try both _gorilla_csrf and sid cookies
                csrf_token = None
                for cookie in self.session.cookies:
                    if cookie.name == '_gorilla_csrf':
                        csrf_token = cookie.value
                        logger.info(f"Found _gorilla_csrf cookie: {csrf_token[:20]}...")
                        break
                    elif cookie.name == 'sid':
                        # Fallback to sid if _gorilla_csrf not found
                        csrf_token = cookie.value

                if csrf_token:
                    # Harbor expects CSRF token in X-Harbor-CSRF-Token header
                    self.session.headers.update({
                        'X-Harbor-CSRF-Token': csrf_token
                    })
                    logger.info(f"Retrieved Harbor CSRF token successfully")
                else:
                    logger.warning(f"No CSRF cookie found, may cause issues")
            else:
                logger.warning(f"Failed to get Harbor system info: {response.status_code}")

        except Exception as e:
            logger.warning(f"Failed to get CSRF token: {e}")

    def check_project_exists(self, project_name: str) -> bool:
        """
        Check if Harbor project exists

        Args:
            project_name: Project name to check

        Returns:
            True if project exists, False otherwise
        """
        try:
            url = f"{self.api_base}/projects/{project_name}"
            response = self._make_request('GET', url)

            if response.status_code == 200:
                logger.info(f"Harbor project '{project_name}' exists")
                return True
            elif response.status_code == 404:
                logger.info(f"Harbor project '{project_name}' does not exist")
                return False
            else:
                logger.warning(f"Unexpected status {response.status_code} checking project")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check Harbor project: {e}")
            raise ValueError(f"Harbor connection failed: {str(e)}")

    def create_project(
        self,
        project_name: str,
        public: bool = False,
        enable_content_trust: bool = False,
        auto_scan: bool = True,
        severity: str = "high",
        prevent_vul: bool = False
    ) -> Dict:
        """
        Create new Harbor project

        Args:
            project_name: Project name (lowercase, alphanumeric, - _ allowed)
            public: Make project public (default: False - private)
            enable_content_trust: Enable Docker Content Trust (image signing)
            auto_scan: Auto scan images on push (default: True)
            severity: Vulnerability severity threshold (critical, high, medium, low)
            prevent_vul: Prevent vulnerable images from running

        Returns:
            Dict with project info

        Raises:
            ValueError: If project creation fails
        """
        try:
            url = f"{self.api_base}/projects"

            # Build project metadata
            metadata = {}
            if enable_content_trust:
                metadata["enable_content_trust"] = "true"
            if auto_scan:
                metadata["auto_scan"] = "true"
            if severity:
                metadata["severity"] = severity
            if prevent_vul:
                metadata["prevent_vul"] = "true"

            # Build request payload
            payload = {
                "project_name": project_name,
                "public": public
            }

            if metadata:
                payload["metadata"] = metadata

            # Make POST request without session/cookies to bypass CSRF
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            response = self._make_request(
                'POST',
                url,
                json=payload,
                headers=headers,
                timeout=30
            )

            # Log response for debugging
            logger.info(f"Harbor create project response: status={response.status_code}")
            if response.status_code != 201:
                try:
                    logger.error(f"Harbor error response: {response.text}")
                except:
                    pass

            if response.status_code == 201:
                # Success - get location header
                location = response.headers.get('Location', '')
                logger.info(f"Harbor project '{project_name}' created successfully")

                return {
                    "project_name": project_name,
                    "location": location,
                    "public": public,
                    "metadata": metadata
                }

            elif response.status_code == 409:
                raise ValueError(f"Project '{project_name}' already exists")

            elif response.status_code == 400:
                error_msg = response.json().get('errors', [{}])[0].get('message', 'Invalid request')
                raise ValueError(f"Invalid project configuration: {error_msg}")

            elif response.status_code == 401:
                raise ValueError("Authentication failed. Check Harbor credentials.")

            elif response.status_code == 403:
                # Try to get more detailed error message
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get('errors', [{}])[0].get('message', '')
                    if error_msg:
                        logger.error(f"Harbor 403 error details: {error_msg}")
                        raise ValueError(f"Permission denied: {error_msg}")
                except:
                    pass
                raise ValueError("Permission denied. User must be Harbor admin with 'Project Admin' or 'System Admin' role.")

            else:
                raise ValueError(f"Project creation failed with status {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Harbor project: {e}")
            raise ValueError(f"Harbor API error: {str(e)}")

    def get_project_info(self, project_name: str) -> Optional[Dict]:
        """
        Get detailed project information

        Args:
            project_name: Project name

        Returns:
            Project info dict or None if not found
        """
        try:
            url = f"{self.api_base}/projects/{project_name}"
            response = self._make_request('GET', url)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get project info: {e}")
            return None

    def list_projects(self, page: int = 1, page_size: int = 10) -> List[Dict]:
        """
        List all Harbor projects

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 10)

        Returns:
            List of project dicts
        """
        try:
            url = f"{self.api_base}/projects"
            params = {
                "page": page,
                "page_size": page_size
            }

            response = self._make_request('GET', url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list projects: {e}")
            return []
