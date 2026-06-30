import os
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

security = HTTPBearer()

async def get_clerk_public_keys():
    """Fetch Clerk's public JWKS for JWT verification."""
    clerk_secret = os.environ["CLERK_SECRET_KEY"]
    # Extract instance from secret key  sk_test_xxx → xxx
    instance = clerk_secret.split("_")[2][:12]
    async with httpx.AsyncClient() as client:
        response = await client.get(os.environ["CLERK_JWKS_URL"])
        return response.json()

async def verify_clerk_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Verify Clerk JWT and return the payload (includes user_id)."""
    token = credentials.credentials
    try:
        jwks = await get_clerk_public_keys()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")