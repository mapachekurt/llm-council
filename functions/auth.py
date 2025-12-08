"""
Authentication utilities for verifying Clerk JWT tokens
"""
import jwt
import requests
from functools import lru_cache

# Clerk's JWKS endpoint
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"

@lru_cache(maxsize=1)
def get_clerk_public_keys():
    """
    Fetch Clerk's public keys for JWT verification
    Cached to avoid repeated requests
    """
    try:
        response = requests.get(CLERK_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Clerk public keys: {e}")
        return None

def verify_clerk_token(token: str, clerk_secret_key: str) -> dict:
    """
    Verify a Clerk JWT token and return the decoded payload

    Args:
        token: The JWT token to verify
        clerk_secret_key: Clerk secret key for verification

    Returns:
        dict: Decoded token payload with user information

    Raises:
        Exception: If token is invalid or verification fails
    """
    try:
        # For development, we can decode without verification (NOT FOR PRODUCTION)
        # In production, you should verify using Clerk's public keys

        # First, try to decode to get the algorithm
        unverified_payload = jwt.decode(token, options={"verify_signature": False})

        # Get the public keys from Clerk
        jwks = get_clerk_public_keys()
        if not jwks:
            raise Exception("Unable to fetch Clerk public keys")

        # Get the kid from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        if not kid:
            raise Exception("Token missing 'kid' in header")

        # Find the matching key
        matching_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                matching_key = key
                break

        if not matching_key:
            raise Exception(f"No matching key found for kid: {kid}")

        # Convert JWK to PEM format
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend

        # Extract the public key components
        n = int.from_bytes(
            jwt.utils.base64url_decode(matching_key['n'].encode()),
            byteorder='big'
        )
        e = int.from_bytes(
            jwt.utils.base64url_decode(matching_key['e'].encode()),
            byteorder='big'
        )

        # Create an RSA public key
        public_numbers = rsa.RSAPublicNumbers(e, n)
        public_key = public_numbers.public_key(default_backend())

        # Convert to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Verify and decode the token
        decoded = jwt.decode(
            token,
            pem,
            algorithms=['RS256'],
            options={"verify_signature": True}
        )

        return decoded

    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Invalid token: {str(e)}")
    except Exception as e:
        raise Exception(f"Token verification failed: {str(e)}")

def extract_user_id(decoded_token: dict) -> str:
    """
    Extract the user ID from a decoded Clerk token

    Args:
        decoded_token: The decoded JWT payload

    Returns:
        str: The user ID
    """
    # Clerk stores the user ID in the 'sub' claim
    user_id = decoded_token.get('sub')
    if not user_id:
        raise Exception("Token missing 'sub' claim")
    return user_id
