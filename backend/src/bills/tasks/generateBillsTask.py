from src.celery.celery_app import celery_app
from globals.utils.logger import logger
from jinja2 import Environment, FileSystemLoader
import os
from src.bills.services.pdfService import PDFService
from db.postgres.connection import PostgresClient
import time
from globals.config.config import BUSINESS_NAME_PLACEHOLDER


template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(loader=FileSystemLoader(template_dir))
usage_tpl = env.get_template("usageBill.html")
fixed_tpl = env.get_template("fixedBill.html")


@celery_app.task(name="bills.generate_images_for_due_date", bind=True, max_retries=2)
def generate_images_for_due_date(self, bills_full_data_for_due_date, chunk_size=25):
    """Celery task: render bill images for a due_date and upload to GCS."""
    try:
        total_bills = len(bills_full_data_for_due_date)
        logger.info(f"Processing {total_bills} bills in chunks of {chunk_size}")

        start_time = time.time()
        # Split bills into chunks
        chunks = [
            bills_full_data_for_due_date[i:i + chunk_size] 
            for i in range(0, total_bills, chunk_size)
        ]
        
        chunks = [
            bills_full_data_for_due_date[i:i + chunk_size] 
            for i in range(0, total_bills, chunk_size)
        ]
        
        total_processed = 0
        total_failed = 0
        failed_bills = []
        
        # Process chunks sequentially (single worker benefit)
        for i, chunk in enumerate(chunks, 1):
            try:
                logger.info(f"Processing chunk {i}/{len(chunks)} ({len(chunk)} bills)")
                
                with PostgresClient.get_sync_session() as session:
                    chunk_processed = 0
                    chunk_failed = 0
                    
                    for bill in chunk:
                        try:
                            bill["business_name"] = BUSINESS_NAME_PLACEHOLDER
                            PDFService.generate_single_bill_jpg_sync(
                                bill_data=bill,
                                usage_template=usage_tpl,
                                fixed_template=fixed_tpl,
                                session=session
                            )
                            chunk_processed += 1
                            
                        except Exception as bill_error:
                            chunk_failed += 1
                            bill_id = bill.get('bill_id', 'unknown')
                            failed_bills.append(str(bill_id))
                            logger.error(f"Failed to process bill {bill_id}: {bill_error}")
                    
                    total_processed += chunk_processed
                    total_failed += chunk_failed
                    
                    logger.info(f"Chunk {i} completed: {chunk_processed} processed, {chunk_failed} failed")
                    
            except Exception as chunk_error:
                logger.error(f"Chunk {i} failed entirely: {chunk_error}")
                total_failed += len(chunk)
                failed_bills.extend([str(b.get('bill_id', 'unknown')) for b in chunk])
        
        return {
            "status": "completed",
            "total_bills": total_bills,
            "processed": total_processed,
            "failed": total_failed,
            "failed_bills": failed_bills,
            "chunks_processed": len(chunks),
            "processing_time": f"{time.time() - start_time} seconds"
        }
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        