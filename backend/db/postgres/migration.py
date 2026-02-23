# migrations.py
from pathlib import Path
from sqlalchemy import create_engine, inspect
from alembic import command
from alembic.config import Config
from globals.utils.logger import logger
import asyncio
from globals.config.config import ASYNC_POSTGRES_DATABASE_URL

SYNC_DATABASE_URL =  ASYNC_POSTGRES_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
BASE_DIR = Path(__file__).resolve().parent.parent.parent  
ALEMBIC_DIR = BASE_DIR / "alembic"


def get_alembic_config() -> Config:
    cfg = Config()  # no alembic.ini required
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)
    # Optional: log level
    # cfg.set_main_option("log_file", "alembic.log")
    return cfg


def ensure_baseline_once():
    """
    If this DB has never been versioned by Alembic, create an empty revision and stamp it.
    This prevents Alembic from trying to 'create all tables' for an already-existing schema.
    """
    engine = create_engine(SYNC_DATABASE_URL)
    insp = inspect(engine)

    if "alembic_version" not in insp.get_table_names():
        cfg = get_alembic_config()
        # command.stamp(cfg, "head")
        command.upgrade(cfg, "head")


def upgrade_to_head():
    """Apply migrations to latest revision."""
    cfg = get_alembic_config()
    command.upgrade(cfg, "head")


# (Optional, for local dev only) generate a new migration from model diffs
def autogenerate_revision(message: str = "autogen"):
    cfg = get_alembic_config()
    command.revision(cfg, message=message, autogenerate=True)


def apply_migrations():
    ensure_baseline_once()
    upgrade_to_head()



async def apply_migrations_with_retry(max_retries: int = 3, delay_seconds: int = 30) -> bool:
    """
    Apply database migrations with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay_seconds: Delay between retries in seconds (default: 30)
        
    Returns:
        bool: True if migrations applied successfully, False otherwise
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Applying database migrations... (Attempt {attempt}/{max_retries})")
            apply_migrations()
            logger.info("Database migrations applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying database migrations (Attempt {attempt}/{max_retries}): {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {delay_seconds} seconds...")
                await asyncio.sleep(delay_seconds)
            else:
                logger.error(f"Failed to apply database migrations after {max_retries} attempts")
                return False
    
    return False


# UPDATE alembic_version SET version_num = '049d28490c78';
# alembic revision -m "migrate_existing_payments_to_new_table"      create a new empty migration file
# alembic revision --autogenerate -m "create_all_tables"            create a new migration file with changes detected automatically
# alembic upgrade head
# alembic downgrade 683818a75e4c


