from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from db.postgres.base import Base
from globals.config.config import ASYNC_POSTGRES_DATABASE_URL

from db.postgres.tables.users import Users
from db.postgres.tables.rates import Rates
from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters
from db.postgres.tables.readings import Readings
from db.postgres.tables.bills import Bills
from db.postgres.tables.areas import Areas
from db.postgres.tables.whatsapp_session import WhatsAppSession
from db.postgres.tables.templates import Templates
from db.postgres.tables.otp import OTP
from db.postgres.tables.fixes import Fixes
from db.postgres.tables.passwordReset import PasswordReset
from db.postgres.tables.payments import Payments
from db.postgres.tables.refresh_tokens import RefreshTokens

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

SYNC_DATABASE_URL =  ASYNC_POSTGRES_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        {
            "sqlalchemy.url": SYNC_DATABASE_URL
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # detect column type changes
            compare_server_default=True,  # detect default changes
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
