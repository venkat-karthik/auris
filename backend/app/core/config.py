"""
Auris - Core Configuration
All environment variables. Single source of truth.
"""
import os
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()


# ── App ───────────────────────────────────────────────────────────────────────
APP_NAME = "Auris"
APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")  # local | production
DEBUG = ENVIRONMENT == "local"

# ── URLs ──────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://auris:auris@localhost:5432/auris")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or (ENVIRONMENT == "production" and JWT_SECRET == "change-me-in-production"):
    if ENVIRONMENT == "production":
        raise RuntimeError("JWT_SECRET must be configured with a secure key in production!")
    else:
        JWT_SECRET = "change-me-in-production-local-only-key-12345"

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "720"))

# ── Storage ───────────────────────────────────────────────────────────────────
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "minio")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "auris-audio")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
# Directory for local call recordings (used when STORAGE_BACKEND is local)
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "/app/recordings")

# ── AI Providers ──────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")

# ── Telephony ─────────────────────────────────────────────────────────────────
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "platform-connection-id")
TELNYX_CALLER_ID = os.getenv("TELNYX_CALLER_ID", "+10000000000")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID", "")

# ── Payments ──────────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# ── TURN / WebRTC ─────────────────────────────────────────────────────────────
TURN_HOST = os.getenv("TURN_HOST", "localhost")
TURN_SECRET = os.getenv("TURN_SECRET", "")
TURN_PORT = int(os.getenv("TURN_PORT", "3478"))

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
