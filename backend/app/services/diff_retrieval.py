import httpx
from typing import Optional
import logging
from backend.app.core.config import settings

logger = logging.getLogger("cris.diff_service")

class GitHubDiffService:
    """
    Service responsible for fetching raw pull request diff streams from GitHub API.
    """
    
    def __init__(self, token: Optional[str] = None):
        # Uses provided token or falls back to system settings
        self.token = token or settings.GITHUB_TOKEN

    async def fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Fetches the unified diff file of a GitHub pull request.
        Makes an authenticated GET request with the media type: application/vnd.github.v3.diff
        """
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "CRIS-App"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            logger.debug("Configuring Authenticated GitHub Authorization Header")
        else:
            logger.warning("No GITHUB_TOKEN configured. Authenticating as Anonymous client (Rate limit restricted)")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                raise HTTPException_like_error(
                    f"GitHub API Error [{response.status_code}]: {response.text}"
                )
                
            return response.text

    async def fetch_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        """
        Fetches base64-encoded source file content from the GitHub repository at a specific commit ref.
        """
        import base64
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CRIS-App"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException_like_error(
                    f"GitHub Content Fetch Error [{response.status_code}]: {response.text}"
                )
            
            data = response.json()
            content_b64 = data.get("content", "")
            
            # Remove line breaks from base64 string and decode
            clean_b64 = content_b64.replace("\n", "").replace("\r", "")
            decoded_bytes = base64.b64decode(clean_b64)
            return decoded_bytes.decode("utf-8")

class HTTPException_like_error(Exception):
    pass

