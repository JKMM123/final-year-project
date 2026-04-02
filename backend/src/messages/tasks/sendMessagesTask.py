from src.celery.celery_app import celery_app
from globals.utils.logger import logger
from jinja2 import Template
import asyncio
from src.messages.services.whatsappMessagesService import WhatsappMessagesService
from db.gcs.gcsService import GCSManager
from globals.config.config import BUCKET_NAME

@celery_app.task(name="templates.send_messages")
def send_messages_task(customers_to_notify, template, user_phone_number):
    """Celery task: send messages using the messaging service."""
    
    async def _send_all_messages(user_phone_number):
        try:
            logger.info(f"Sending messages to {len(customers_to_notify)} customers.")
            whatsapp_messages_service = WhatsappMessagesService()
            gcs_manager = GCSManager()  
            
            jinja_template = Template(template)
            results = []
            
            for customer in customers_to_notify:
                try:
                    personalized_message = jinja_template.render(**customer)
                    phone_number = customer.get('customer_phone_number')
                    blob_name = customer.get('blob_name', None)
                    
                    await asyncio.sleep(5.5)

                    if blob_name:
                        signed_url = gcs_manager.generate_signed_url(
                            bucket_name=BUCKET_NAME,
                            blob_name=blob_name,
                            expiration_minutes=200
                        )
                        logger.info(f"Sending image message to {phone_number}")
                        await whatsapp_messages_service.send_whatsapp_message(phone_number, personalized_message, image_url=signed_url)
                    else:
                        logger.info(f"Sending text message to {phone_number}")
                        await whatsapp_messages_service.send_whatsapp_message(phone_number, personalized_message)

                    results.append({
                        "customer_id": customer.get('meter_id'),
                        "phone_number": phone_number,
                        "status": "sent",
                        "message": personalized_message
                    })

                except Exception as customer_error:
                    logger.error(f"Failed to process customer {customer.get('meter_id')}: {customer_error}")
                    results.append({
                        "customer_id": customer.get('meter_id'),
                        "status": "failed",
                        "error": str(customer_error)
                    })
                    continue
            
            success_count = len([r for r in results if r["status"] == "sent"])
            failure_count = len(results) - success_count
            
            logger.info(f"Message sending completed. Sent: {success_count}, Failed: {failure_count}")
            message = f"Messages task completed. Sent: {success_count}, Failed: {failure_count}"
            await asyncio.sleep(5.5)
            await whatsapp_messages_service.send_whatsapp_message(user_phone_number, message)

            return {
                "status": "completed",
                "messages_sent": success_count,
                "failed_messages": failure_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in send_messages: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "messages_sent": 0,
                "failed_messages": len(customers_to_notify) if customers_to_notify else 0
            }
    
    # Run all messages in a single async context
    return asyncio.run(_send_all_messages(user_phone_number))

