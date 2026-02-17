import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GitHubService:
    @staticmethod
    def create_repository(
        name: str,
        owner: str,
        pat: str,
        visibility: str = "public",
        is_org: bool = False
    ) -> Optional[str]:
        """
        Creates a new GitHub repository using the GitHub API.
        Returns the clone URL if successful, None otherwise.
        """
        if not pat:
            logger.error("GitHub PAT is required to create a repository.")
            return None

        # Determine the endpoint: /user/repos or /orgs/{org}/repos
        # We'll try to detect if it's an org or user. 
        # For simplicity, we can try to get the user context first or just assume based on input.
        # Let's try to see if 'owner' matches the PAT holder.
        
        headers = {
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Check if owner is the authenticated user
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            logger.error(f"Failed to authenticate with GitHub PAT: {user_resp.text}")
            return None
        
        auth_user = user_resp.json()["login"]
        
        data = {
            "name": name,
            "private": visibility == "private"
        }

        if owner.lower() == auth_user.lower():
            url = "https://api.github.com/user/repos"
        else:
            url = f"https://api.github.com/orgs/{owner}/repos"

        logger.info(f"Creating repository '{name}' for owner '{owner}' via {url}")
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            clone_url = repo_data.get("clone_url")
            logger.info(f"Successfully created repository: {clone_url}")
            return clone_url
        elif response.status_code == 422:
            error_data = response.json()
            if any(err.get("message") == "name already exists on this account" for err in error_data.get("errors", [])):
                logger.info(f"Repository '{name}' already exists. Fetching existing repo details.")
                # Fetch existing repo info
                repo_url = f"https://api.github.com/repos/{owner}/{name}"
                repo_resp = requests.get(repo_url, headers=headers)
                if repo_resp.status_code == 200:
                    clone_url = repo_resp.json().get("clone_url")
                    logger.info(f"Using existing repository: {clone_url}")
                    return clone_url
                else:
                    logger.error(f"Failed to fetch existing repository details: {repo_resp.text}")
                    return None
            
            logger.error(f"Failed to create repository (422): {response.text}")
            return None
        else:
            logger.error(f"Failed to create repository: {response.status_code} - {response.text}")
            return None
