from celery import Celery
from celery.signals import worker_init, worker_shutdown
from globals.utils.logger import logger
from globals.config.config import REDIS_HOST, REDIS_PORT

celery_app = Celery(
    "billing_system",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
)

celery_app.conf.imports = [
    "src.bills.tasks.generateBillsTask",
    "src.bills.tasks.downloadBillsTask",
    "src.messages.tasks.sendMessagesTask",
]

celery_app.conf.update(

    # Resource optimization
    task_acks_late=True,
    worker_prefetch_multiplier=1,    # Perfect for concurrency=1 - one task at a time

    # Failure tolerance
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    result_expires=60*60*60,

    # Retry configuration
    task_retry_jitter=False,
    # task_retry_jitter_max=30,

    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Memory optimization
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks

    # Timezone
    timezone="UTC",
    enable_utc=True,
)

@worker_init.connect
def _on_worker_init(**kwargs):
    from db.postgres.connection import PostgresClient
    try:
        PostgresClient.init_sync_engine() 
        logger.info("Celery worker DB engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to init DB engine in worker: {e}")

@worker_shutdown.connect
def _on_worker_shutdown(**kwargs):
    from db.postgres.connection import PostgresClient
    try:
        PostgresClient.close_sync_engine()  
        logger.info("Celery worker DB engine closed successfully.")
    except Exception as e:
        logger.error(f"Failed to close DB engine in worker: {e}")