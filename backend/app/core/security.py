import hmac
import hashlib
from fastapi import Request, HTTPException
from backend.app.core.config import settings

def verify_api_key(api_key: str) -> bool:
    """
    Placeholder function to verify incoming client access keys/tokens.
    To be implemented in subsequent phases.
    """
    return True

async def verify_github_signature(request: Request):
    """
    Dependency validator checking X-Hub-Signature-256 header to authenticate GitHub calls.
    Computes HMAC SHA256 signature from body content and raises 401 on validation failures.
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 signature header is missing")
        
    parts = signature_header.split("=")
    if len(parts) != 2 or parts[0] != "sha256":
        raise HTTPException(status_code=401, detail="Invalid signature header format. Must be sha256=hash")
        
    received_hash = parts[1]
    body_bytes = await request.body()
    
    # Calculate signature using SHA256 digest
    computed_hash = hmac.new(
        key=settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing side-channel attacks
    if not hmac.compare_digest(received_hash, computed_hash):
        raise HTTPException(status_code=401, detail="HMAC-SHA256 signature mismatch verification failed")
