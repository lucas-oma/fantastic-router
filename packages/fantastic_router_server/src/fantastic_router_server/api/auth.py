"""
Authentication and API key validation middleware
"""

import hashlib
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
import json
import os

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)

class APIKeyValidator:
    """Validates API keys against the system database"""
    
    def __init__(self, system_db_url: str):
        self.system_db_url = system_db_url

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        try:
            conn = psycopg2.connect(self.system_db_url)
            cursor = conn.cursor()
            
            # Check if API key exists and is active
            cursor.execute("""
                SELECT ak.id, ak.key_name, ak.permissions, ak.rate_limit_per_minute, ak.expires_at,
                       u.id as user_id, u.username, u.email, u.role
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                                       WHERE ak.api_key = %s AND ak.is_active = true AND u.is_active = true
            """, (api_key,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Check if API key is expired
            if result[4] and time.time() > result[4].timestamp():
                return None
            
            # Update last_used_at
            cursor.execute("""
                UPDATE api_keys 
                SET last_used_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (result[0],))
            
            conn.commit()
            
            return {
                "api_key_id": result[0],
                "key_name": result[1],
                "permissions": result[2] or {},
                "rate_limit_per_minute": result[3],
                "user_id": result[5],
                "username": result[6],
                "email": result[7],
                "role": result[8]
            }
            
        except Exception as e:
            print(f"Error validating API key: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def check_rate_limit(self, api_key_id: str) -> bool:
        """Check if API key is within rate limits"""
        try:
            conn = psycopg2.connect(self.system_db_url)
            cursor = conn.cursor()
            
            # Get current minute window
            current_minute = int(time.time() / 60) * 60
            
            # Get rate limit for this API key
            cursor.execute("""
                SELECT rate_limit_per_minute FROM api_keys WHERE id = %s
            """, (api_key_id,))
            
            # TODO: remove or hash api keys when printing to console
            result = cursor.fetchone()
            if not result:
                print(f"API key {api_key_id} not found in database")
                return False
                
            rate_limit = result[0]
            if rate_limit is None or rate_limit <= 0:
                print(f"Infinite rate limit for API key {api_key_id}: {rate_limit}")
                return True
            
            # First check current usage
            cursor.execute("""
                SELECT request_count FROM rate_limits 
                WHERE api_key_id = %s AND window_start = to_timestamp(%s)
            """, (api_key_id, current_minute))
            
            result = cursor.fetchone()
            current_count = result[0] if result else 0
            
            print(f"Rate limit check: API key {api_key_id}, limit: {rate_limit}, current: {current_count}")
            
            # Check if we would exceed the limit
            if current_count >= rate_limit:
                print(f"Rate limit exceeded: {current_count} >= {rate_limit}")
                return False
            
            # Increment usage (safe to do now)
            cursor.execute("""
                INSERT INTO rate_limits (api_key_id, window_start, request_count)
                VALUES (%s, to_timestamp(%s), 1)
                ON CONFLICT (api_key_id, window_start)
                DO UPDATE SET request_count = rate_limits.request_count + 1
            """, (api_key_id, current_minute))
            
            conn.commit()
            print(f"Rate limit updated: {current_count + 1} requests this minute")
            return True
            
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

# Global validator instance
# TODO: use ENV variable for system db url
_system_db_url = os.getenv('SYSTEM_DATABASE_URL', 'postgresql://system_user:system_pass@localhost:5433/fantastic_router_system')
api_key_validator = APIKeyValidator(_system_db_url)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to validate API key and get current user"""
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required. For testing scripts, you can set FR_API_KEY environment variable: export FR_API_KEY=your_api_key_here",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    user_info = api_key_validator.validate_api_key(api_key)
    
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check rate limit
    if not api_key_validator.check_rate_limit(user_info["api_key_id"]):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )
    
    return user_info

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Optional dependency to validate API key (doesn't require it)"""
    
    if not credentials:
        return None
    
    api_key = credentials.credentials
    user_info = api_key_validator.validate_api_key(api_key)
    
    if user_info:
        # Check rate limit only if API key is valid
        if not api_key_validator.check_rate_limit(user_info["api_key_id"]):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
            )
    
    return user_info 