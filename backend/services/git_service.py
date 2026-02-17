import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class GitService:
    @staticmethod
    def verify_access(repo_url: str, pat: str = None) -> bool:
        """
        Verifies access to a remote repository.
        Tries without PAT first if it's a public repo, otherwise uses PAT.
        """
        def check(url, p=None):
            cmd = ["git", "ls-remote", url, "HEAD"]
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"
            
            url_to_use = url
            if p and url.startswith("https://"):
                clean_url = url[len("https://"):]
                url_to_use = f"https://{p}@{clean_url}"
                cmd[2] = url_to_use

            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                env=env,
                timeout=15
            )
            return result.returncode == 0

        # 1. Try without PAT first (to avoid issues with public repos and irrelevant PATs)
        if check(repo_url):
            return True
        
        # 2. Try with PAT if provided
        if pat:
            return check(repo_url, pat)
            
        return False

    @staticmethod
    def get_branches(repo_url: str, pat: str = None) -> list[str]:
        """
        Fetches remote branches. Falls back to no-PAT if PAT fails on public repo.
        """
        def fetch(url, p=None):
            cmd = ["git", "ls-remote", "--heads", url]
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"
            
            url_to_use = url
            if p and url.startswith("https://"):
                clean_url = url[len("https://"):]
                url_to_use = f"https://{p}@{clean_url}"
                cmd[3] = url_to_use

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=20
            )
            return result

        # 1. Try with PAT if provided
        result = fetch(repo_url, pat) if pat else fetch(repo_url)
        
        # 2. If it failed and we used a PAT, try without it (could be a public repo)
        if result.returncode != 0 and pat:
            logger.info("Branch fetch with PAT failed, retrying without auth...")
            result = fetch(repo_url)

        if result.returncode != 0:
            logger.error(f"Failed to fetch branches: {result.stderr}")
            return []

        branches = []
        for line in result.stdout.splitlines():
            parts = line.split('\t')
            if len(parts) == 2:
                ref = parts[1]
                branch_name = ref.replace('refs/heads/', '')
                branches.append(branch_name)
        return branches

    @staticmethod
    def clone_repo(repo_url: str, dest_path: str, pat: str = None, branch: str = None) -> bool:
        """
        Clones a repository. Falls back to no-PAT if PAT fails on public repo.
        """
        def do_clone(url, p=None):
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])
            
            url_to_use = url
            if p and url.startswith("https://"):
                clean_url = url[len("https://"):]
                url_to_use = f"https://{p}@{clean_url}"
            
            cmd.extend([url_to_use, dest_path])
            
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"

            return subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=120
            )

        # 1. Try with PAT if provided
        result = do_clone(repo_url, pat) if pat else do_clone(repo_url)
        
        # 2. Fallback if PAT failed on a potentially public repo
        if result.returncode != 0 and pat:
            # Check if directory was created and is empty or needs cleanup
            if os.path.exists(dest_path):
                try:
                    import shutil
                    if os.path.isdir(dest_path):
                        shutil.rmtree(dest_path)
                    else:
                        os.remove(dest_path)
                except Exception as e:
                    logger.warning(f"Cleanup failed during clone fallback: {e}")
            
            logger.info("Clone with PAT failed, retrying without auth...")
            result = do_clone(repo_url)

        if result.returncode == 0:
            logger.info(f"Successfully cloned {repo_url} into {dest_path}")
            return True
        else:
            logger.error(f"Failed to clone {repo_url}: {result.stderr}")
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

    @staticmethod
    def create_branch(repo_path: str, branch_name: str, base_branch: str = "main") -> bool:
        """
        Creates a new branch from a base branch in a local repository.
        """
        if not base_branch:
            base_branch = "main"
            
        try:
            # 1. Try to checkout base branch
            logger.info(f"Checking out base branch '{base_branch}' in {repo_path}")
            checkout_res = subprocess.run(["git", "checkout", base_branch], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if checkout_res.returncode != 0:
                logger.warning(f"Could not checkout '{base_branch}', attempting to create it: {checkout_res.stderr.strip()}")
                # Try to create it if it doesn't exist (might be a new repo)
                subprocess.run(["git", "checkout", "-b", base_branch], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            else:
                # 2. Pull latest (only if checkout succeeded)
                try:
                    subprocess.run(["git", "pull", "origin", base_branch], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except:
                    logger.warning(f"Could not pull latest for {base_branch}")

            # 3. Create new migration branch
            logger.info(f"Creating new migration branch '{branch_name}'")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name} from {base_branch}: {str(e)}")
            return False

    @staticmethod
    def push_branch(repo_path: str, branch_name: str) -> bool:
        """
        Pushes a local branch to the remote 'origin'.
        """
        try:
            logger.info(f"Pushing branch {branch_name} to origin")
            subprocess.run(["git", "push", "origin", branch_name], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            logger.error(f"Failed to push branch {branch_name} to origin: {str(e)}")
            return False
