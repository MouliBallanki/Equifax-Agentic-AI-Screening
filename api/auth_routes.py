"""
Authentication Routes.

Signup, Login, and user profile endpoints using JWT tokens.
"""

import logging
import os
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "equifax-screening-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _create_token(user_id: str, first_name: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "first_name": first_name,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _get_db_url() -> str:
    return os.getenv("DATABASE_URL", "mysql://root:password@localhost:3306/equifax_screening")


# --------------- Request / Response schemas ---------------

class SignupRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6)
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# --------------- Endpoints ---------------

@auth_router.post("/signup")
async def signup(req: SignupRequest) -> Dict[str, Any]:
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    from tools.database_tool import DatabaseTool

    db_tool = DatabaseTool(_get_db_url())
    try:
        await db_tool.connect()
        async with db_tool.pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT user_id FROM users WHERE email = %s", (req.email,))
                if await cursor.fetchone():
                    raise HTTPException(status_code=409, detail="Email already registered")

                user_id = str(uuid.uuid4())
                password_hash = _hash_password(req.password)

                await cursor.execute(
                    "INSERT INTO users (user_id, first_name, email, password_hash) VALUES (%s, %s, %s, %s)",
                    (user_id, req.first_name, req.email, password_hash),
                )
                await conn.commit()

        logger.info(f"User registered: {req.email}")
        return {"status": "success", "message": "Account created successfully", "user_id": user_id}
    finally:
        await db_tool.disconnect()


@auth_router.post("/login")
async def login(req: LoginRequest) -> Dict[str, Any]:
    from tools.database_tool import DatabaseTool

    db_tool = DatabaseTool(_get_db_url())
    try:
        await db_tool.connect()
        async with db_tool.pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT user_id, first_name, email, password_hash FROM users WHERE email = %s",
                    (req.email,),
                )
                user = await cursor.fetchone()

        if not user or not _verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = _create_token(user["user_id"], user["first_name"], user["email"])
        return {
            "status": "success",
            "token": token,
            "user_id": user["user_id"],
            "first_name": user["first_name"],
            "email": user["email"],
        }
    finally:
        await db_tool.disconnect()


@auth_router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(authorization[7:])

    return {
        "user_id": payload["sub"],
        "first_name": payload["first_name"],
        "email": payload["email"],
    }
