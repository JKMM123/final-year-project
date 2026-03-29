from src.celery.celery_app import celery_app
from globals.utils.logger import logger
from jinja2 import Environment, FileSystemLoader
import os
from src.bills.services.pdfService import PDFService
import tempfile
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import asyncio
from wasenderapi.errors import WasenderAPIError
from globals.config.config import BUCKET_NAME
from src.messages.services.whatsappMessagesService import WhatsappMessagesService
import time
from globals.config.config import BUSINESS_NAME_PLACEHOLDER


template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(loader=FileSystemLoader(template_dir))
usage_tpl = env.get_template("usageBill.html")
fixed_tpl = env.get_template("fixedBill.html")


@celery_app.task(name="bills.generate_combined_pdf_for_due_date", bind=True, max_retries=2)
def generate_pdfs_for_due_date(self, bills_full_data_for_due_date, user_phone_number):
    """
    Generate a single PDF with multiple bills per page (4 bills per page)
    Much more efficient than individual PDFs
    """
    try:
        total_bills = len(bills_full_data_for_due_date)
        logger.info(f"Generating combined PDF with {total_bills} bills (4 per page)")
        
        if total_bills == 0:
            return {"status": "completed", "processed": 0, "download_url": None}

        start_time = time.time()
        
        # Add business name to all bills
        for bill_data in bills_full_data_for_due_date:
            bill_data["business_name"] = BUSINESS_NAME_PLACEHOLDER
        
        # Generate combined PDF
        download_url = PDFService.generate_combined_bills_pdf(
            bills_data=bills_full_data_for_due_date,
            usage_template=usage_tpl,
            fixed_template=fixed_tpl,
            bills_per_page=4
        )
        
        if not download_url:
            raise Exception("Failed to generate PDF")
        
        # Send WhatsApp notification
        whatsapp_messages_service = WhatsappMessagesService()
        try:
            asyncio.run(
                whatsapp_messages_service.send_whatsapp_message(
                    phone_number=user_phone_number,
                    message=f"Your combined PDF with {total_bills} bills is ready for download"
                )
            )
        except Exception as e:
            logger.error(f"WhatsApp notification failed: {e}")
            # Don't fail the task for notification errors
        
        processing_time = time.time() - start_time
        logger.info(f"Combined PDF generation completed in {processing_time:.2f} seconds")
        
        return {
            "status": "completed",
            "total_bills": total_bills,
            "bills_per_page": 4,
            "total_pages": (total_bills + 3) // 4,  # Ceiling division
            "download_url": download_url,
            "processing_time": f"{processing_time:.2f} seconds"
        }
        
    except Exception as e:
        logger.error(f"Combined PDF generation task failed: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

