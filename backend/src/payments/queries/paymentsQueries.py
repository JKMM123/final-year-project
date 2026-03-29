from db.postgres.tables import payments
from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, update, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional
from db.postgres.tables.meters import Meters

from datetime import datetime, date
from db.postgres.tables.payments import Payments 
from db.postgres.tables.bills import Bills
from db.postgres.tables.rates import Rates

from src.payments.schemas.createPaymentSchema import CreatePaymentSchema
from src.payments.schemas.updatePaymentSchema import UpdatePaymentSchema
from src.payments.schemas.searchPaymentsSchema import SearchPaymentsSchema
from src.payments.exceptions.exceptions import (
    PaymentNotFoundError,
    BillNotFoundError,
    MeterNotFoundError,
    BillAlreadyPaidError,
    InvalidPaymentAmountError,
    PaymentExceedsBillAmountError,
)
from src.rates.exceptions.exec import (
    RateNotFoundError
)
from src.rates.queries.ratesQueries import RatesQueries

class PaymentsQueries:
    def __init__(self):
        self.rates_queries = RatesQueries()
        logger.info("Payments Queries initialized successfully.")
        

    async def create_payment(self, session: AsyncSession, payment_data):
        """Create a new Payments record"""
        try:
            # Verify Bills exists
            bill_query = select(Bills).where(Bills.bill_id == payment_data.get('bill_id'))
            bill_result = await session.execute(bill_query)
            bill = bill_result.scalar_one_or_none()

            if not bill:
                logger.error(f"Bills with ID {payment_data.get('bill_id')} not found.")
                raise BillNotFoundError(f"Bill not found")
            
            total_paid_usd = bill.total_paid_usd
            total_paid_lbp = bill.total_paid_lbp

            if total_paid_usd >= bill.amount_due_usd and total_paid_lbp >= bill.amount_due_lbp:
                logger.error(f"Bill {payment_data.get('bill_id')} is already fully paid")
                raise BillAlreadyPaidError(f"Bill {payment_data.get('bill_id')} is already fully paid")
                        
            # Check if Payment amount exceeds remaining Bill amount
            remaining_amount_usd = bill.amount_due_usd - total_paid_usd
            remaining_amount_lbp = bill.amount_due_lbp - total_paid_lbp

            rates = await self.rates_queries.get_rates_by_id(rate_id=bill.rate_id, session=session)
            dollar_rate = rates.get('dollar_rate')
            
            payment_usd = payment_data.get('amount_usd', None)
            payment_lbp = payment_data.get('amount_lbp', None)

            if payment_usd:
                payment_lbp = payment_usd * dollar_rate
                payment_usd = round(payment_usd, 2)

            else:
                payment_usd = payment_lbp / dollar_rate
                payment_usd = round(payment_usd, 2)

            if payment_usd > remaining_amount_usd:
                logger.error(f"Payment amount USD {payment_usd} exceeds remaining bill amount {remaining_amount_usd}")
                raise PaymentExceedsBillAmountError(f"Payment amount USD exceeds remaining bill amount")
                
            # if payment_lbp > remaining_amount_lbp:
            #     logger.error(f"Payment amount LBP {payment_lbp} exceeds remaining bill amount {remaining_amount_lbp}")
            #     raise PaymentExceedsBillAmountError(f"Payment amount LBP exceeds remaining bill amount")

            # Create Payments record
            payment = Payments(
                bill_id=payment_data.get('bill_id'),
                meter_id=bill.meter_id,
                amount_lbp=payment_lbp,
                amount_usd=payment_usd,
                payment_method=payment_data.get('payment_method'),
                payment_date=payment_data.get('payment_date'),
                created_by=payment_data.get('created_by'),
                updated_by=payment_data.get('created_by')
            )

            session.add(payment)

            # update bills table
            bill.total_paid_usd = round(bill.total_paid_usd + payment_usd, 2)
            bill.total_paid_lbp = int(bill.total_paid_lbp + payment_lbp)

            bill.updated_by = payment_data.get('created_by')

            if bill.total_paid_usd >= bill.amount_due_usd:
                bill.status = "paid"
            else:
                bill.status = "partially_paid"

            session.add(bill)

            await session.commit()

            logger.info(f'Payment created successfully for bill {payment_data.get("bill_id")}')
            return {
                "bill_id": str(payment.bill_id),
                "meter_id": str(payment.meter_id),
                "amount_lbp": str(payment.amount_lbp),
                "amount_usd": str(payment.amount_usd),
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
            }
        except RateNotFoundError:
            raise

        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error creating payment: {e}")
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating payment: {e}")
            raise


    async def get_payment_by_id(self, session: AsyncSession, payment_id: int) -> Optional[Payments]:
        """Get Payments by ID with joined Bills and Meters information"""
        query = (
            select(
                Payments,
            )
            .where(Payments.payment_id == payment_id)
        )
        
        result = await session.execute(query)
        payment = result.scalar_one_or_none()

        if not payment:
            logger.error(f"Payment with ID {payment_id} not found.")
            raise PaymentNotFoundError(f"Payment not found")
        
        logger.info(f"Payment {payment_id} retrieved successfully.")
        
        return {
            "payment_id": str(payment.payment_id),
            "bill_id": str(payment.bill_id),
            "meter_id": str(payment.meter_id),
            "amount_lbp": str(payment.amount_lbp),
            "amount_usd": str(payment.amount_usd),
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date.isoformat(),
        }
        

    async def get_bill_by_id(self, bill_id, session: AsyncSession):
        try:
            bill_query = select(Bills).where(Bills.bill_id == bill_id)
            bill_result = await session.execute(bill_query)
            bill = bill_result.scalar_one_or_none()
            if not bill:
                logger.error(f"Bill with ID {bill_id} not found.")
                raise BillNotFoundError()
            
            logger.info(f"Bill {bill_id} retrieved successfully.")
            return bill
        
        except Exception as e:
            logger.error(f"Error fetching bill: {e}")
            raise

    
    async def update_payment(
        self,
        session: AsyncSession, 
        payment_id: str, 
        payment_data: dict
    ):
        """Update an existing Payments"""
        try:
            # Get existing Payments
            payment_query = select(Payments).where(Payments.payment_id == payment_id)
            payment_result = await session.execute(payment_query)
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                logger.error(f"Payment with ID {payment_id} not found.")
                raise PaymentNotFoundError()
            
            bill = await self.get_bill_by_id(payment.bill_id, session)
            rates = await self.rates_queries.get_rates_by_id(rate_id=bill.rate_id, session=session)
            dollar_rate = rates.get('dollar_rate')

            # Store original payment amounts to revert bill totals
            original_payment_lbp = int(payment.amount_lbp)
            original_payment_usd = round(payment.amount_lbp, 2)
             

            # Process new payment amounts
            entered_amount_lbp = payment_data.get('amount_lbp', None)
            entered_amount_usd = payment_data.get('amount_usd', None)

            new_amount_lbp = 0
            new_amount_usd = 0

            # Calculate missing amount using exchange rate
            if entered_amount_usd is not None and entered_amount_lbp is None:
                new_amount_lbp = int(entered_amount_usd) * dollar_rate
                new_amount_usd = float(entered_amount_usd)
                new_amount_usd = round(new_amount_usd, 2)
                logger.info(f"Calculated amount_lbp: {new_amount_lbp} from amount_usd: {entered_amount_usd}")
            elif entered_amount_lbp is not None and entered_amount_usd is None:
                new_amount_usd = float(entered_amount_lbp) / dollar_rate
                new_amount_usd = round(new_amount_usd, 2)
                new_amount_lbp = int(entered_amount_lbp)
                logger.info(f"Calculated amount_usd: {new_amount_usd} from amount_lbp: {entered_amount_lbp}")

            # Calculate bill status after reverting the original payment
            bill_without_this_payment_lbp = int(bill.total_paid_lbp) - original_payment_lbp
            bill_without_this_payment_usd = float(bill.total_paid_usd) - original_payment_usd

            # Calculate remaining amounts available for payment (after removing this payment)
            remaining_amount_lbp = int(bill.amount_due_lbp) - bill_without_this_payment_lbp
            remaining_amount_usd = float(bill.amount_due_usd) - bill_without_this_payment_usd

            # Validate new payment doesn't exceed remaining bill amount
            if entered_amount_lbp is not None and new_amount_lbp > remaining_amount_lbp:
                logger.error(f"New payment amount LBP {new_amount_lbp} exceeds remaining bill amount {remaining_amount_lbp}")
                raise PaymentExceedsBillAmountError(f"Payment amount LBP {new_amount_lbp} exceeds remaining bill amount {remaining_amount_lbp}")
                
            if entered_amount_usd is not None and new_amount_usd > remaining_amount_usd:
                logger.error(f"New payment amount USD {new_amount_usd} exceeds remaining bill amount {remaining_amount_usd}")
                raise PaymentExceedsBillAmountError(f"Payment amount USD {new_amount_usd} exceeds remaining bill amount {remaining_amount_usd}")

            total_paid_lbp = bill_without_this_payment_lbp + new_amount_lbp
            total_paid_usd = bill_without_this_payment_usd + new_amount_usd

            amount_due_lbp = bill.amount_due_lbp
            amount_due_usd = bill.amount_due_usd

            # Update bill status
            if total_paid_usd <= 0:
                bill.status = "unpaid"
            elif total_paid_usd >= float(amount_due_usd):
                bill.status = "paid"
            else:
                bill.status = "partially_paid"

            bill.total_paid_lbp = total_paid_lbp
            bill.total_paid_usd = total_paid_usd
            bill.updated_by = payment_data.get('updated_by')

            session.add(bill)

            # Update payment record
            payment.amount_lbp = new_amount_lbp
            payment.amount_usd = new_amount_usd
            
            # Update other payment fields if provided
            if 'payment_method' in payment_data:
                payment.payment_method = payment_data['payment_method']
            if 'payment_date' in payment_data:
                payment.payment_date = payment_data['payment_date']
            if 'updated_by' in payment_data:
                payment.updated_by = payment_data['updated_by']

            session.add(payment)
            await session.commit()
            await session.refresh(payment)

            logger.info(f"Payment {payment_id} updated successfully")
            
            return {
                "payment_id": str(payment.payment_id),
                "bill_id": str(payment.bill_id),
                "meter_id": str(payment.meter_id),
                "amount_lbp": str(payment.amount_lbp),
                "amount_usd": str(payment.amount_usd),
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating payment: {e}")
            raise 
    

    async def delete_payment(self, session: AsyncSession, payment_id: int) -> bool:
        """Delete a Payments record"""
        try:
            payment_query = select(Payments).where(Payments.payment_id == payment_id)
            payment_result = await session.execute(payment_query)
            payment = payment_result.scalar_one_or_none()
            
            if not payment:
                logger.error(f'Payment with id: {payment_id} not found for deletion.')
                raise PaymentNotFoundError()
            
            bill = await self.get_bill_by_id(payment.bill_id, session)

            amount_lbp = payment.amount_lbp
            amount_usd = payment.amount_usd

            bill.total_paid_lbp -= int(amount_lbp)
            bill.total_paid_usd -= float(amount_usd)
            bill.updated_by = payment.updated_by

            if bill.total_paid_usd <= 0 and bill.total_paid_lbp <= 0:
                bill.status = "unpaid"

            else:
                bill.status='partially_paid'

            await session.delete(payment)
            await session.commit()

            logger.info(f'Payment with id: {payment_id} deleted successfully.')
            return True
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting payment {payment_id}: {e}")
            raise
    

    async def get_all_payments_by_bill_id(self, session: AsyncSession, bill_id: int) -> dict:
        """Get Payments summary for a specific Bills"""
        try:
            # Get Bills info
            bill_query = select(Bills).where(Bills.bill_id == bill_id)
            bill_result = await session.execute(bill_query)
            bill = bill_result.scalar_one_or_none()
            
            if not bill:
                raise BillNotFoundError()
            
            # Get Payments summary
            payments_query = (
                select(
                    Payments
                )
                .where(Payments.bill_id == bill_id)
            )
            
            payments_result = await session.execute(payments_query)
            payments = payments_result.scalars().all()
            
            payments_list = [
                {
                    "payment_id": str(payment.payment_id),
                    "amount_lbp": str(payment.amount_lbp),
                    "amount_usd": str(payment.amount_usd),
                    "payment_method": payment.payment_method,
                    "payment_date": payment.payment_date.isoformat(),
                }
                for payment in payments
            ]
            return payments_list
        
        except Exception as e:
            logger.error(f"Error fetching payments for bill ID {bill_id}: {e}")
            raise


    async def mark_all_bills_as_paid(
            self,
            meter_id: str,
            payment_method: str,
            created_by: str,
            session: AsyncSession,
    ):
        """Mark all bills for a given meter as paid"""

        try:
            # Verify meter exists
            meter_query = select(Meters).where(Meters.meter_id == meter_id)
            meter_result = await session.execute(meter_query)
            meter = meter_result.scalar_one_or_none()

            if not meter:
                logger.error(f"Meter with ID {meter_id} not found.")
                raise MeterNotFoundError(f"Meter not found")

            # Get all unpaid and partially paid bills for this meter
            bills_query = select(Bills).where(
                and_(
                    Bills.meter_id == meter_id,
                    Bills.status.in_(["unpaid", "partially_paid"])
                )
            )
            bills_result = await session.execute(bills_query)
            bills = bills_result.scalars().all()

            if not bills:
                logger.info(f"No unpaid bills found for meter {meter_id}")
                return {
                    "status": "completed",
                    "message": "No unpaid bills found",
                    "bills_processed": 0,
                    "payments_created": 0
                }

            payments_created = 0
            bills_processed = 0

            current_date = datetime.now().date()

            for bill in bills:
                try:
                    # Calculate remaining amount to pay
                    remaining_amount_usd = bill.amount_due_usd - bill.total_paid_usd
                    remaining_amount_lbp = bill.amount_due_lbp - bill.total_paid_lbp

                    # Skip if already fully paid (safety check)
                    if remaining_amount_usd <= 0 and remaining_amount_lbp <= 0:
                        continue

                    # Get exchange rate for this bill
                    rates = await self.rates_queries.get_rates_by_id(rate_id=bill.rate_id, session=session)
                    dollar_rate = rates.get('dollar_rate')

                    # Create payment for the remaining amount
                    payment = Payments(
                        bill_id=bill.bill_id,
                        meter_id=meter_id,
                        amount_lbp=remaining_amount_lbp,
                        amount_usd=remaining_amount_usd,
                        payment_method=payment_method,
                        payment_date=current_date,
                        created_by=created_by,
                        updated_by=created_by
                    )

                    session.add(payment)

                    # Update bill to paid status
                    bill.total_paid_usd = bill.amount_due_usd
                    bill.total_paid_lbp = bill.amount_due_lbp
                    bill.status = "paid"
                    bill.updated_by = created_by

                    session.add(bill)
                    
                    payments_created += 1
                    bills_processed += 1

                    logger.debug(f"Created payment for bill {bill.bill_id}, amount: {remaining_amount_usd} USD / {remaining_amount_lbp} LBP")

                except Exception as bill_error:
                    logger.error(f"Failed to process bill {bill.bill_id}: {bill_error}")
                    continue

            await session.commit()

            logger.info(f"Successfully marked {bills_processed} bills as paid for meter {meter_id}")
            return {
                "status": "completed",
                "message": f"Successfully processed {bills_processed} bills",
                "bills_processed": bills_processed,
                "payments_created": payments_created,
                "meter_id": str(meter_id)
            }

        except MeterNotFoundError:
            raise

        except RateNotFoundError:
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in mark_all_bills_as_paid: {str(e)}")
            raise
