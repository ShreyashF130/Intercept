# backend/app/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from backend.app.database import supabase_client

X_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def authenticate_tenant(api_key: str = Security(X_API_KEY_HEADER)):
    """
    Intercepts and authenticates inbound traffic against active organization profiles in Supabase.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. X-API-Key header is missing."
        )

    try:
        # Perform targeted fetch for the unique tenant key
        response = supabase_client.table("organizations").select("id, name, tier, is_active").eq("api_key", api_key).execute()
        records = response.data

        if not records:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. The provided API key is invalid or has expired."
            )

        tenant = records[0]

        if not tenant.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Your organization profile is currently deactivated."
            )

        # Return clean metadata context dict to the router endpoint
        return {
            "organization_id": tenant["id"],
            "organization_name": tenant["name"],
            "tier": tenant["tier"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication Gateway Exception: Unable to verify system keys."
        )

# --- BACKWARD COMPATIBILITY ALIAS ---
# This ensures legacy routes (telemetry.py, dashboard.py) can still import their expected name
verify_api_key = authenticate_tenant