import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class GitService:
    @staticmethod
    def verify_access(repo_url: str, pat: str = None) -> bool:
        """
        Verifies access to a remote repository using git ls-remote.
        """
        try:
            cmd = ["git", "ls-remote", repo_url, "HEAD"]
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo" # Dummy echo to silence askpass if any
            
            # If PAT is provided, we might need to inject it into the URL or use standard git credential helpers.
            # For simplicity, if PAT is provided, we assume the URL might need modification or the environment 
            # is set up. However, inserting PAT into URL is the most direct way for HTTPS.
            # https://<PAT>@github.com/user/repo.git
            
            if pat:
                # Basic sanitation to ensure we don't double inject or mess up protocol
                if repo_url.startswith("https://"):
                   # Strip https:// 
                   clean_url = repo_url[len("https://"):]
                   # Inject pat@
                   auth_url = f"https://{pat}@{clean_url}"
                   cmd[2] = auth_url

            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                env=env,
                timeout=15 # Increased timeout slightly
            )
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"Git access failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Git verify exception: {str(e)}")
            return False

    @staticmethod
    def get_branches(repo_url: str, pat: str = None) -> list[str]:
        """
        Fetches remote branches using git ls-remote.
        """
        try:
            cmd = ["git", "ls-remote", "--heads", repo_url]
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo" # Dummy echo to silence askpass if any
            
            if pat:
                 # Basic sanitation to ensure we don't double inject or mess up protocol
                if repo_url.startswith("https://"):
                   # Strip https:// 
                   clean_url = repo_url[len("https://"):]
                   # Inject pat@
                   auth_url = f"https://{pat}@{clean_url}"
                   cmd[3] = auth_url

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=20
            )

            if result.returncode != 0:
                logger.error(f"Failed to fetch branches: {result.stderr}")
                return []

            branches = []
            for line in result.stdout.splitlines():
                parts = line.split('\t')
                if len(parts) == 2:
                    ref = parts[1]
                    # ref is likely 'refs/heads/branch_name'
                    branch_name = ref.replace('refs/heads/', '')
                    branches.append(branch_name)
            
            return branches

        except Exception as e:
            logger.error(f"Git get_branches exception: {str(e)}")
            return []
