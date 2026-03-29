from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from src.payments.queries.paymentsQueries import PaymentsQueries
from src.payments.schemas.createPaymentSchema import CreatePaymentSchema
from src.payments.schemas.updatePaymentSchema import UpdatePaymentSchema
from src.payments.schemas.getPaymentSchema import GetPaymentSchema, GetPaymentsByBillSchema
from src.payments.schemas.deletePaymentSchema import DeletePaymentSchema
from src.payments.schemas.searchPaymentsSchema import SearchPaymentsSchema
from src.payments.schemas.markBillsAsPaidSchema import MarkBillsAsPaidSchema

from src.payments.exceptions.exceptions import (
    PaymentNotFoundError,
    PaymentExceedsBillAmountError,
    BillNotFoundError,
    BillAlreadyPaidError
)


class PaymentsService:
    def __init__(self):
        self.payments_queries = PaymentsQueries()
        logger.info("Payments Service initialized successfully.")
    

    async def create_payment(
        self,
        request: Request,
        session: AsyncSession,
    ):
        """Create a new payment"""
        # Validate request 
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreatePaymentSchema
            )
        if not valid:
            logger.error(f"Validation failed in create_payment: {validated_request}")
            raise ValidationError(errors=validated_request)
        try:            
            token = request.state.user
            payment_data = validated_request.get('body')
            payment_data['created_by'] = token.get('user_id')

            # Create payment
            payment = await self.payments_queries.create_payment(session, payment_data)
            
            logger.info(f"Payment created successfully with ID: {payment.get('payment_id')}")
            return success_response(
                data=payment,
                message="Payment created successfully"
            )
        
        except (
            BillNotFoundError,
            PaymentExceedsBillAmountError,
            BillAlreadyPaidError
            ):
            raise

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise InternalServerError(f"Failed to create payment: {str(e)}")
    

    async def get_payment_by_id(
        self,
        request: Request,
        session: AsyncSession,
    ):
        """Get payment by ID"""
        # Validate request 
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPaymentSchema
            )
        if not valid:
            logger.error(f"Validation failed in create_payment: {validated_request}")
            raise ValidationError(errors=validated_request)
            
        try:
            payment_id = validated_request.get('path').get('payment_id')
            # Get payment
            payment = await self.payments_queries.get_payment_by_id(session, payment_id)
            
            logger.info(f"Payment retrieved successfully with ID: {payment_id}")
            return success_response(
                data=payment,
                message="Payment retrieved successfully"
            )
        
        except (
            PaymentNotFoundError
        ):
            raise
            
        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}")
            raise InternalServerError(f"Failed to retrieve payment. ")


    async def get_all_payments_by_bill_id(
        self,
        request: Request,
        session: AsyncSession,
    ):
        """Get payment summary for a specific bill"""

        valid, validated_request = await validate_request(
            request=request,
            query_model=GetPaymentsByBillSchema
            )
        if not valid:
            logger.error(f"Validation failed in get_all_payments_by_bill_id: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            bill_id = validated_request.get('query').get('bill_id')
            payments = await self.payments_queries.get_all_payments_by_bill_id(session, bill_id)

            logger.info(f"Payment summary retrieved for bill ID: {bill_id}")
            return success_response(
                data=payments,
                message="Payments retrieved successfully"
            )
        
        except BillNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"Error getting get_all_payments_by_bill_id: {str(e)}")
            raise InternalServerError(f"Failed to retrieve all payments for bill. ")


    async def delete_payment(
        self,
        request: Request,
        session: AsyncSession,
    ):
        """Delete a payment"""
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPaymentSchema
            )
        if not valid:
            logger.error(f"Validation failed in create_payment: {validated_request}")
            raise ValidationError(errors=validated_request)
        try:
            payment_id = validated_request.get('path').get('payment_id')
            result = await self.payments_queries.delete_payment(session, payment_id)
            
            logger.info(f"Payment deleted successfully with ID: {payment_id}")
            return success_response(
                data=[],
                message="Payment deleted successfully"
            )
        
        except (
            PaymentNotFoundError,
            BillNotFoundError
            ):
            raise
            
        except Exception as e:
            logger.error(f"Error deleting payment: {str(e)}")
            raise InternalServerError(f"Failed to delete payment")


    async def update_payment(
        self,
        request: Request,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Update an existing payment"""
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPaymentSchema,
            body_model=UpdatePaymentSchema
            )
        if not valid:
            logger.error(f"Validation failed in create_payment: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user
            payment_id = validated_request.get('path').get('payment_id')
            payment_data = validated_request.get('body')

            # Update payment
            payment = await self.payments_queries.update_payment(session, payment_id, payment_data)
                        
            logger.info(f"Payment updated successfully with ID: {payment_id}")
            return success_response(
                data=payment,
                message="Payment updated successfully"
            )
            
        except (
            PaymentNotFoundError,
            BillNotFoundError,
            PaymentExceedsBillAmountError
            ):
            raise

        except Exception as e:
            logger.error(f"Error updating payment: {str(e)}")
            raise InternalServerError(f"Failed to update payment")
    

    async def mark_all_bills_as_paid(
            self,
            request: Request,
            session: AsyncSession,
    ):
        
        valid, validated_request = await validate_request(
            request=request,
            query_model=MarkBillsAsPaidSchema
        )
        if not valid:
            logger.error(f"Validation failed in create_payment: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            token = request.state.user
            meter_id = validated_request.get('query').get('meter_id')
            payment_method = validated_request.get('query').get('payment_method')
            result = await self.payments_queries.mark_all_bills_as_paid(
                session=session, 
                created_by=token.get('user_id'),
                payment_method=payment_method,
                meter_id=meter_id
                )

            logger.info(f"All bills marked as paid for meter ID: {meter_id}")
            return success_response(
                data=result,
                message="All bills marked as paid successfully"
            )

        except Exception as e:
            logger.error(f"Error in mark_all_bills_as_paid: {str(e)}")
            raise InternalServerError(f"Failed to mark all bills as paid")

    