import os
import json
from google.cloud import secretmanager
from dotenv import load_dotenv
import base64
from globals.utils.logger import logger


load_dotenv()


env = "dev"

if env == "prod":
    secret_file_path = os.getenv("SECRETS_BASE64_FILE_PATH")
    if not secret_file_path:
        raise RuntimeError("Environment variable SECRETS_BASE64_FILE_PATH not set")

    with open(secret_file_path, "r") as f:
        SECRETS_BASE64_FILE = f.read().strip()

    SYSTEM_SECRETS = json.loads(base64.b64decode(SECRETS_BASE64_FILE))

else:
    # secret_file_path = os.getenv("DEV_SECRETS_BASE64_FILE_PATH")
    # if not secret_file_path:
    #     raise RuntimeError("Environment variable DEV_SECRETS_BASE64_FILE_PATH not set")

    # with open(secret_file_path, "r") as f:
    #     DEV_SECRETS_BASE64_FILE = f.read().strip()

    # SECRETS = json.loads(base64.b64decode(DEV_SECRETS_BASE64_FILE))

    SYSTEM_SECRETS = os.getenv("SECRETS_BASE64")
    SYSTEM_SECRETS = json.loads(base64.b64decode(SYSTEM_SECRETS))


if not SYSTEM_SECRETS:
    raise RuntimeError("System secrets not found")

FRONT_END_URL = SYSTEM_SECRETS.get("FRONT_END_URL")
if not FRONT_END_URL:
    raise RuntimeError("Front end URL not found")

# postgres configuration
ASYNC_POSTGRES_DATABASE_URL = SYSTEM_SECRETS.get("ASYNC_POSTGRES_DATABASE_URL", None)
if not ASYNC_POSTGRES_DATABASE_URL:
    raise RuntimeError("Postgres database URL not found")

# system configuration
SYSTEM_CONFIG = SYSTEM_SECRETS.get("system", None)
if not SYSTEM_CONFIG:
    raise RuntimeError("System configuration not found")

SYSTEM_USER_PHONE_NUMBER = SYSTEM_CONFIG.get("SYSTEM_USER_PHONE_NUMBER")
SYSTEM_USERNAME = SYSTEM_CONFIG.get("SYSTEM_USERNAME", "system")
SYSTEM_PASSWORD = SYSTEM_CONFIG.get("SYSTEM_PASSWORD")
DEFAULT_PASSWORD = SYSTEM_CONFIG.get("DEFAULT_PASSWORD")
BUSINESS_NAME_PLACEHOLDER = SYSTEM_CONFIG.get("BUSINESS_NAME_PLACEHOLDER")


# JWT configuration
JWT_CONFIG = SYSTEM_SECRETS.get("jwt", None)
if not JWT_CONFIG:
    raise RuntimeError("JWT configuration not found")

JWT_SECRET_KEY = JWT_CONFIG.get("JWT_SECRET_KEY")
JWT_ALGORITHM = JWT_CONFIG.get("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(JWT_CONFIG.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = int(
    JWT_CONFIG.get("JWT_REFRESH_TOKEN_EXPIRE_MINUTES")
)

# GCS configuration
GCS_SERVICE_ACCOUNT = SYSTEM_SECRETS.get("GCS_SERVICE_ACCOUNT", None)
if not GCS_SERVICE_ACCOUNT:
    raise RuntimeError("GCS service account not found")

PROJECT_ID = GCS_SERVICE_ACCOUNT.get("project_id")
if not PROJECT_ID:
    raise RuntimeError("GCS project ID not found in service account")

BUCKET_NAME = f"electricity-billing-system-bucket-{PROJECT_ID}"
print(f"GCS bucket name: {BUCKET_NAME}")


# redis configuration
REDIS_CONFIG = SYSTEM_SECRETS.get("redis", None)
if not REDIS_CONFIG:
    raise RuntimeError("Redis configuration not found")

print(f"Redis configuration: {REDIS_CONFIG}")

REDIS_HOST = REDIS_CONFIG.get("REDIS_HOST")
REDIS_PORT = REDIS_CONFIG.get("REDIS_PORT")
REDIS_PASSWORD = REDIS_CONFIG.get("REDIS_PASSWORD")
REDIS_DB = REDIS_CONFIG.get("REDIS_DB")
REDIS_USERNAME = REDIS_CONFIG.get("REDIS_USERNAME", None)

# WhatsApp configuration
WHATSAPP_CONFIG = SYSTEM_SECRETS.get("WHATSAPP", None)
if not WHATSAPP_CONFIG:
    raise RuntimeError("WhatsApp configuration not found")
WA_SENDER_API_PAT = WHATSAPP_CONFIG.get("WA_SENDER_API_PAT")
WA_WEBHOOK_URL = WHATSAPP_CONFIG.get("WA_WEBHOOK_URL")

# WKHTML configuration
WKHTML_CONFIG = SYSTEM_SECRETS.get("WKHTML", None)
if not WKHTML_CONFIG:
    raise RuntimeError("WKHTML configuration not found")
WKHTMLTOPDF_BIN = WKHTML_CONFIG.get("WKHTMLTOPDF_BIN")
WKHTMLTOIMAGE_BIN = WKHTML_CONFIG.get("WKHTMLTOIMAGE_BIN")

logger.info("Configuration loaded successfully.")
