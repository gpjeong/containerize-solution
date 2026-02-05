"""Jenkins API client for triggering builds and updating pipeline scripts"""
import logging
import xml.etree.ElementTree as ET
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
            logger.debug(f"Fetching crumb from: {crumb_url}")

            response = self.session.get(crumb_url, timeout=10)

            logger.debug(f"Crumb response status: {response.status_code}")
            logger.debug(f"Crumb response headers: {response.headers}")

            if response.status_code == 404:
                # CSRF protection is not enabled
                logger.info("Jenkins CSRF protection is not enabled (no crumb required)")
                return None

            # Check if we got HTML instead of JSON (authentication issue)
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error("Received HTML response instead of JSON when fetching crumb - authentication may have failed")
                logger.error(f"Response content: {response.text[:500]}")
                raise ValueError("Authentication failed: Jenkins returned HTML instead of JSON")

            response.raise_for_status()
            data = response.json()

            crumb = {
                data.get('crumbRequestField', 'Jenkins-Crumb'): data.get('crumb', '')
            }

            logger.info(f"Retrieved Jenkins crumb successfully: {list(crumb.keys())[0]}")
            logger.debug(f"Crumb value: {list(crumb.values())[0][:20]}...")
            return crumb

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Jenkins crumb: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text[:500]}")
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

    def verify_job_exists(self, job_name: str) -> bool:
        """
        Verify that a Jenkins job exists

        Args:
            job_name: Jenkins job name

        Returns:
            bool: True if job exists

        Raises:
            ValueError: If job does not exist
        """
        try:
            job_url = f"{self.base_url}/job/{job_name}/api/json"
            logger.debug(f"Verifying job exists: {job_url}")

            response = self.session.get(job_url, timeout=10)

            if response.status_code == 404:
                raise ValueError(f"Jenkins job '{job_name}' not found. Please create the job first.")

            # Check if we got HTML instead of JSON
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error("Received HTML response when checking job - authentication or permission issue")
                logger.error(f"Response content: {response.text[:500]}")
                raise ValueError("Authentication or permission error: Cannot access Jenkins job")

            response.raise_for_status()
            logger.info(f"Job '{job_name}' exists and is accessible")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to verify job exists: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text[:500]}")
            raise

    def update_pipeline_script(self, job_name: str, pipeline_script: str) -> bool:
        """
        Update Jenkins Pipeline Job의 스크립트

        Uses a simple approach: replace entire config with new pipeline script

        Args:
            job_name: Jenkins job name
            pipeline_script: Groovy pipeline script content

        Returns:
            bool: Success status

        Raises:
            requests.exceptions.RequestException: Jenkins API 호출 실패
        """
        try:
            # First verify the job exists
            self.verify_job_exists(job_name)

            config_url = f"{self.base_url}/job/{job_name}/config.xml"
            logger.info(f"Updating job config at: {config_url}")

            # Log the original pipeline script for debugging
            logger.debug("="*80)
            logger.debug("ORIGINAL PIPELINE SCRIPT:")
            logger.debug(pipeline_script)
            logger.debug("="*80)

            # Create complete config XML with new pipeline script
            config_xml = self.create_pipeline_config_xml(pipeline_script)

            # Log the generated XML for debugging
            logger.debug("="*80)
            logger.debug("GENERATED CONFIG XML:")
            logger.debug(config_xml)
            logger.debug("="*80)

            # Prepare headers with crumb if available
            headers = {"Content-Type": "application/xml"}
            if self.crumb:
                headers.update(self.crumb)
                logger.debug(f"Using crumb headers: {self.crumb}")

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

            # Log response details for debugging
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text[:500]}")

                # Check if it's a 404 (job doesn't exist)
                if e.response.status_code == 404:
                    raise ValueError(f"Jenkins job '{job_name}' not found. Please create the job first.")

                # 500 error - likely XML or script issue
                if e.response.status_code == 500:
                    raise ValueError(f"Jenkins server error (500). This usually means the config XML is invalid or the Pipeline script has syntax errors. Check Jenkins logs for details.")

            raise

    def trigger_build(self, job_name: str) -> Dict:
        """
        Trigger a build for the given job

        Args:
            job_name: Jenkins job name

        Returns:
            dict: Build information including queue ID and build URL

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

            build_info = {
                "job_name": job_name,
                "queue_id": queue_id,
                "queue_url": queue_location,
                "job_url": f"{self.base_url}/job/{job_name}",
                "status": "QUEUED"
            }

            logger.info(f"Build triggered successfully. Queue ID: {queue_id}")
            return build_info

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger build: {e}")
            raise

    def get_build_number_from_queue(self, queue_id: str) -> Optional[int]:
        """
        Get build number from queue item

        Args:
            queue_id: Jenkins queue item ID

        Returns:
            int: Build number if available, None if still queued
        """
        try:
            queue_url = f"{self.base_url}/queue/item/{queue_id}/api/json"
            response = self.session.get(queue_url, timeout=10)

            if response.status_code == 404:
                # Queue item might have been processed
                return None

            response.raise_for_status()
            data = response.json()

            # Check if build has started
            executable = data.get('executable', {})
            if executable:
                return executable.get('number')

            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to get build number from queue: {e}")
            return None

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
