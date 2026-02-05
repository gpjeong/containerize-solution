"""Jenkins API client for triggering builds and updating pipeline scripts"""
import logging
from typing import Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class JenkinsClient:
    """Client for interacting with Jenkins REST API"""

    def __init__(self, jenkins_url: str, username: str, api_token: str, verify_ssl: bool = False):
        """
        Initialize Jenkins client

        Args:
            jenkins_url: Jenkins server URL (e.g., http://jenkins.example.com:8080)
            username: Jenkins username
            api_token: Jenkins API token
            verify_ssl: Whether to verify SSL certificates (default: False for self-signed certs)
        """
        self.base_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, api_token)
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = self.verify_ssl

        if not self.verify_ssl:
            logger.warning("SSL certificate verification is disabled. This is insecure in production!")

        # Get Jenkins crumb for CSRF protection
        self.crumb = self._get_crumb()

    def _get_crumb(self) -> Optional[Dict[str, str]]:
        """
        Get Jenkins crumb for CSRF protection

        Returns:
            dict: Crumb header and value, or None if crumb is not required
        """
        try:
            crumb_url = f"{self.base_url}/crumbIssuer/api/json"
            response = self.session.get(crumb_url, timeout=10)

            if response.status_code == 404:
                logger.info("Jenkins CSRF protection is not enabled (no crumb required)")
                return None

            # Check if we got HTML instead of JSON (authentication issue)
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error("Received HTML response - authentication may have failed")
                raise ValueError("Authentication failed: Jenkins returned HTML instead of JSON")

            response.raise_for_status()
            data = response.json()

            crumb = {
                data.get('crumbRequestField', 'Jenkins-Crumb'): data.get('crumb', '')
            }

            logger.info(f"Retrieved Jenkins crumb successfully")
            return crumb

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Jenkins crumb: {e}")
            raise

    def create_pipeline_config_xml(self, pipeline_script: str) -> str:
        """
        Create a complete Pipeline job config.xml

        Args:
            pipeline_script: Groovy pipeline script content

        Returns:
            str: Complete Jenkins Pipeline job config XML
        """
        # Use CDATA to avoid XML escaping issues with Groovy script
        config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Auto-generated Pipeline for Docker image build</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.90">
    <script><![CDATA[{pipeline_script}]]></script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""

        return config_xml

    def update_pipeline_script(self, job_name: str, pipeline_script: str) -> bool:
        """
        Update Jenkins Pipeline Job의 스크립트

        Args:
            job_name: Jenkins job name
            pipeline_script: Groovy pipeline script content

        Returns:
            bool: Success status

        Raises:
            requests.exceptions.RequestException: Jenkins API 호출 실패
        """
        try:
            config_url = f"{self.base_url}/job/{job_name}/config.xml"
            logger.info(f"Updating job config at: {config_url}")

            # Create complete config XML with pipeline script
            config_xml = self.create_pipeline_config_xml(pipeline_script)

            # Prepare headers with crumb if available
            headers = {"Content-Type": "application/xml"}
            if self.crumb:
                headers.update(self.crumb)

            # Post new config to Jenkins
            response = self.session.post(
                config_url,
                data=config_xml.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            logger.info(f"Successfully updated job config for: {job_name}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update pipeline script: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text[:500]}")

                if e.response.status_code == 404:
                    raise ValueError(f"Jenkins job '{job_name}' not found. Please create the job first.")

                if e.response.status_code == 500:
                    raise ValueError(f"Jenkins server error (500). Check Jenkins logs for details.")

            raise

    def get_build_number_from_queue(self, queue_id: str, timeout: int = 15) -> Optional[int]:
        """
        Get build number from queue ID by polling

        Args:
            queue_id: Jenkins queue item ID
            timeout: Maximum seconds to wait for build number

        Returns:
            int: Build number if found, None otherwise
        """
        import time

        if not queue_id:
            return None

        try:
            queue_api_url = f"{self.base_url}/queue/item/{queue_id}/api/json"
            logger.info(f"Polling queue item {queue_id} for build number...")

            start_time = time.time()
            poll_interval = 0.5  # Poll every 0.5 seconds for faster response

            while time.time() - start_time < timeout:
                response = self.session.get(queue_api_url, timeout=5)

                # If queue item not found, it might have already completed
                if response.status_code == 404:
                    logger.warning(f"Queue item {queue_id} not found (might have completed quickly)")
                    return None

                response.raise_for_status()
                data = response.json()

                # Check if build has been created (executable field contains build info)
                executable = data.get('executable')
                if executable:
                    build_number = executable.get('number')
                    if build_number:
                        logger.info(f"Found build number: {build_number} for queue ID: {queue_id}")
                        return build_number

                # Wait a bit before next poll
                time.sleep(poll_interval)

            logger.warning(f"Timeout waiting for build number for queue ID: {queue_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get build number from queue: {e}")
            return None

    def get_latest_build_number(self, job_name: str) -> Optional[int]:
        """
        Get the latest build number for a job

        Args:
            job_name: Jenkins job name

        Returns:
            int: Latest build number if found, None otherwise
        """
        try:
            job_api_url = f"{self.base_url}/job/{job_name}/api/json"
            response = self.session.get(job_api_url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                last_build = data.get('lastBuild')
                if last_build:
                    build_number = last_build.get('number')
                    logger.info(f"Latest build number for {job_name}: {build_number}")
                    return build_number

            return None
        except Exception as e:
            logger.error(f"Failed to get latest build number: {e}")
            return None

    def trigger_build(self, job_name: str) -> Dict:
        """
        Trigger a build for the given job

        Args:
            job_name: Jenkins job name

        Returns:
            dict: Build information including queue ID, build number and build URL

        Raises:
            requests.exceptions.RequestException: Jenkins API 호출 실패
        """
        try:
            build_url = f"{self.base_url}/job/{job_name}/build"
            logger.info(f"Triggering build for job: {job_name}")

            # Prepare headers with crumb if available
            headers = {}
            if self.crumb:
                headers.update(self.crumb)

            response = self.session.post(build_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Get queue item location from response header
            queue_location = response.headers.get('Location', '')
            queue_id = queue_location.split('/')[-2] if queue_location else None

            # Try to get build number from queue
            build_number = None
            if queue_id:
                build_number = self.get_build_number_from_queue(queue_id, timeout=15)

            # If still no build number, try getting the latest build number
            if not build_number:
                logger.info(f"Attempting to get latest build number for {job_name}")
                build_number = self.get_latest_build_number(job_name)

            build_info = {
                "job_name": job_name,
                "queue_id": queue_id,
                "queue_url": queue_location,
                "job_url": f"{self.base_url}/job/{job_name}",
                "build_number": build_number,
                "build_url": f"{self.base_url}/job/{job_name}/{build_number}" if build_number else None,
                "status": "BUILDING" if build_number else "QUEUED"
            }

            logger.info(f"Build triggered successfully. Queue ID: {queue_id}, Build Number: {build_number}")
            return build_info

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger build: {e}")
            raise

    def update_and_build(self, job_name: str, pipeline_script: str) -> Dict:
        """
        Update pipeline script and trigger build in one operation

        Args:
            job_name: Jenkins job name
            pipeline_script: Groovy pipeline script content

        Returns:
            dict: Build information

        Raises:
            requests.exceptions.RequestException: Jenkins API 호출 실패
        """
        # Update pipeline script
        self.update_pipeline_script(job_name, pipeline_script)

        # Trigger build
        build_info = self.trigger_build(job_name)

        return build_info


# Global instance (will be created per request)
def create_jenkins_client(jenkins_url: str, username: str, api_token: str, verify_ssl: bool = False) -> JenkinsClient:
    """
    Factory function to create Jenkins client

    Args:
        jenkins_url: Jenkins server URL
        username: Jenkins username
        api_token: Jenkins API token
        verify_ssl: Whether to verify SSL certificates (default: False for self-signed certs)

    Returns:
        JenkinsClient: Configured Jenkins client
    """
    return JenkinsClient(jenkins_url, username, api_token, verify_ssl=verify_ssl)
