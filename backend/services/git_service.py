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

    @staticmethod
    def clone_repo(repo_url: str, dest_path: str, pat: str = None, branch: str = None) -> bool:
        """
        Clones a repository to a destination path.
        """
        try:
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])
            
            # Use original URL in command, will replace if PAT exists
            url_to_use = repo_url
            if pat and repo_url.startswith("https://"):
                clean_url = repo_url[len("https://"):]
                url_to_use = f"https://{pat}@{clean_url}"
            
            cmd.extend([url_to_use, dest_path])
            
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=120 # Cloning can take time
            )

            if result.returncode == 0:
                logger.info(f"Successfully cloned {repo_url} into {dest_path}")
                return True
            else:
                logger.error(f"Failed to clone {repo_url}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Clone exception: {str(e)}")
            return False

    @staticmethod
    def get_head_commit(repo_path: str) -> str:
        """
        Returns the current HEAD commit hash of a local repository.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception as e:
            logger.error(f"Failed to get HEAD commit for {repo_path}: {str(e)}")
            return ""

    @staticmethod
    def init_repo(repo_path: str) -> bool:
        """
        Initializes a new git repository in a folder.
        """
        try:
            result = subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to init repo at {repo_path}: {str(e)}")
            return False
