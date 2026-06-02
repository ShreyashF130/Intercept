import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

# We define the header name developers must use
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# For now, we use a single master key from your .env file.
# Later, this will check the Supabase database for individual user keys.
VALID_API_KEY = os.getenv("INTERCEPT_MASTER_KEY", "sk_test_intercept_123")

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    """
    Blocks any request that does not include the correct API key in the headers.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    
    if api_key_header != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key. Access denied.",
        )
    
    return api_key_header   