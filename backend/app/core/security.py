"""
Auris - Auth / Security
JWT tokens + API key hashing + password hashing. All written from scratch.
"""
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, org_id: int | None = None) -> str:
    payload = {
        "sub": str(user_id),
        "org": org_id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# ── API Keys ──────────────────────────────────────────────────────────────────

def generate_api_key() -> tuple[str, str, str]:
    """Returns (raw_key, key_hash, key_prefix).
    raw_key is shown once to the user. key_hash is stored in DB.
    """
    raw = f"ak_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:12]
    return raw, key_hash, prefix


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Razorpay HMAC ─────────────────────────────────────────────────────────────

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    message = f"{order_id}|{payment_id}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_razorpay_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
