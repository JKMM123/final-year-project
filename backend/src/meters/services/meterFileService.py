from globals.utils.logger import logger
import pandas as pd
from io import StringIO
from src.meters.exceptions.exceptions import (
    InvalidColumnsException,
    EmptyFileException,
    FileProcessingTimeoutException
)
from src.packages.exceptions.exceptions import (
    InvalidPackageError
)

from src.areas.exceptions.exceptions import (
    InvalidAreaNameException
)


from globals.utils.fileValidator import FileValidator, FileValidationConfigs
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from src.meters.schemas.meterFileUploadSchemas import MeterFileUploadRow
from src.meters.queries.metersQueries import MetersQueries
from fastapi import Request, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from typing import Optional


class MeterFileService:
    def __init__(self, meters_queries: MetersQueries):
        self.meters_queries = meters_queries
        logger.info("MeterFileService initialized successfully")


    def _safe_pandas_to_string(self, value, field_name):
        """Convert pandas value to string, handling NaN properly"""
        if pd.isna(value):
            raise ValueError(f"{field_name} cannot be empty")
        
        if isinstance(value, float):
            if field_name == "phone number" and value == int(value):
                return str(int(value))
            return str(value)
        
        return str(value).strip()


    def _safe_pandas_to_int(self, value, field_name):
        """Convert pandas value to int, handling NaN properly"""
        if pd.isna(value):
            raise ValueError(f"{field_name} cannot be empty")
        
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid {field_name}: {value}")


    def process_customers_file(self, file_content: bytes, packages: dict, areas: dict, customers_names_and_phone_numbers: dict, file_type: str):
        """
        Process the content of a CSV file containing customer data.
        """
        try:
   
            if file_type == "CSV":
                csv_string = file_content.decode('utf-8-sig')
                try:
                    meters_df = pd.read_csv(StringIO(csv_string))
                    logger.info(f"CSV loaded successfully. Shape: {meters_df.shape}")
                except pd.errors.EmptyDataError:
                    logger.error("CSV file is an empty file")
                    raise EmptyFileException(
                        file_type="CSV"
                    )
                
            if file_type == "EXCEL":
                try:
                    meters_df = pd.read_excel(file_content, engine='openpyxl')
                    logger.info(f"Excel file loaded successfully. Shape: {meters_df.shape}")
                except pd.errors.EmptyDataError:
                    logger.error("Excel file is an empty file")
                    raise EmptyFileException(
                        file_type="EXCEL"
                    )

            if meters_df.empty:
                logger.error("CSV file is empty or contains no data rows")
                raise EmptyFileException(
                    file_type="CSV"
                )

            meters_df.columns = meters_df.columns.str.strip().str.lower()

            required_columns = [
                "full name",
                "phone number",
                "address",
                "amperage",
                "area",
                "package type",
                "initial reading",
            ]
            missing_columns = [col for col in required_columns if col not in meters_df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                logger.error(f"Available columns: {meters_df.columns.tolist()}")
                raise InvalidColumnsException(required_columns)
            
            amperage_list = set(packages.keys())
            amperage_column_values = meters_df['amperage'].unique()

            # Validate amperage if available in db
            invalid_packages = []
            for amperage in amperage_column_values:
                try:
                    if pd.isna(amperage):
                        invalid_packages.append("empty amperage value")
                        continue
                    amperage = int(amperage)

                    if amperage not in amperage_list:
                        invalid_packages.append(amperage)

                except Exception as e:
                    logger.warning(f"Error processing amperage value {amperage}: {e}")
                    invalid_packages.append(str(amperage))

            if invalid_packages:
                logger.error(f"Invalid packages found: {invalid_packages}")
                logger.error(f"Available packages: {amperage}")
                raise InvalidPackageError(invalid_packages=invalid_packages)
            
            areas_list = set(areas.keys())
            area_column_values = meters_df['area'].unique()
            invalid_areas = []
            for area in area_column_values:
                try:
                    if pd.isna(area):
                        invalid_areas.append("empty area value")
                        continue
                    area = str(area).strip().lower()

                    if area not in areas_list:
                        invalid_areas.append(area)

                except Exception as e:
                    logger.warning(f"Error processing area value {area}: {e}")
                    invalid_areas.append(str(area))

            if invalid_areas:
                logger.error(f"Invalid areas found: {invalid_areas}")
                logger.error(f"Available areas: {areas_list}")
                raise InvalidAreaNameException(
                    invalid_areas=invalid_areas
                )


            # Check for duplicate combinations in the file
            duplicate_errors = []

            # Create a tuple for each row: (full_name, phone_number, address)
            identity_tuples = meters_df[['full name', 'phone number', 'address']].dropna().apply(
                lambda row: (str(row['full name']).strip().lower(), str(row['phone number']).strip(), str(row['address']).strip().lower()), axis=1
            )

            # Find duplicated tuples
            duplicated_identities = identity_tuples[identity_tuples.duplicated(keep='first')]

            if not duplicated_identities.empty:
                for idx, identity in duplicated_identities.items():
                    duplicate_errors.append({
                        "row": idx + 2,
                        "field": "customer identity",
                        "error": f"Duplicate customer found: name='{identity[0]}', phone='{identity[1]}', address='{identity[2]}'"
                    })

            if duplicate_errors:
                logger.error(f"Duplicate customer identity values found: {len(duplicate_errors)} errors")
                raise ValidationError(
                    message="Duplicate customer identity values found in the file",
                    errors=duplicate_errors
                )

            # Check for existing customers in the database
            existing_customer_errors = []

            # Build a set of tuples from the database for fast lookup
            existing_identities = {
                (customer["customer_full_name"].strip().lower(), customer["customer_phone_number"].strip(), customer["address"].strip().lower())
                for customer in customers_names_and_phone_numbers
            }

            for index, row in meters_df.iterrows():
                try:
                    if pd.notna(row['full name']) and pd.notna(row['phone number']) and pd.notna(row['address']):
                        full_name = str(row['full name']).strip().lower()
                        phone_number = str(row['phone number']).strip()
                        address = str(row['address']).strip().lower()
                        identity = (full_name, phone_number, address)
                        if identity in existing_identities:
                            existing_customer_errors.append({
                                "row": index + 2,
                                "field": "customer identity",
                                "error": f"Customer with name '{row['full name']}', phone '{row['phone number']}', and address '{row['address']}' already exists in your customers section."
                            })
                except Exception as e:
                    logger.warning(f"Error checking existing customer in row {index + 2}: {e}")

            if existing_customer_errors:
                logger.error(f"Existing customers found: {len(existing_customer_errors)} errors")
                raise ValidationError(
                    message="Customers already exist in database",
                    errors=existing_customer_errors
                )


            #  Validate each row in the DataFrame
            validated_customers = []
            validation_errors = []

            for index, row in meters_df.iterrows():
                row_errors = []  
            
                try:

                    customer_full_name = None
                    customer_phone_number = None
                    address = None
                    package_id = None
                    package_type = None
                    area_id = None
                    initial_reading = None

                    # Validate full name
                    try:
                        customer_full_name = self._safe_pandas_to_string(row['full name'], "customer name")
                    except ValueError as e:
                        row_errors.append({
                            "field": "full name",
                            "error": str(e)
                        })

                    # Validate phone number
                    try:
                        customer_phone_number = self._safe_pandas_to_string(row['phone number'], "phone number")
                    except ValueError as e:
                        row_errors.append({
                            "field": "phone number",
                            "error": str(e)
                        })

                    # Validate address
                    try:
                        address = self._safe_pandas_to_string(row['address'], "address")
                    except ValueError as e:
                        row_errors.append({
                            "field": "customer address",
                            "error": str(e)
                        })

                    # Validate package type
                    try:
                        package_type = self._safe_pandas_to_string(row['package type'], "package type")
                    except ValueError as e:
                        row_errors.append({
                            "field": "package type",
                            "error": str(e)
                        })

                    # Validate initial reading
                    try:
                        initial_reading = self._safe_pandas_to_int(row['initial reading'], "initial reading")
                    except ValueError as e:
                        row_errors.append({
                            "field": "initial reading",
                            "error": str(e)
                        })

                    # Validate amperage 
                    try:
                        amperage = self._safe_pandas_to_int(row['amperage'], "amperage")
                    except ValueError as e:
                        row_errors.append({
                            "field": "amperage",
                            "error": str(e)
                        })

                    # Validate area
                    try:
                        area = self._safe_pandas_to_string(row['area'], "area")
                    except ValueError as e:
                        row_errors.append({
                            "field": "area",
                            "error": str(e)
                        })

                    if row_errors:
                        for error in row_errors:
                            validation_errors.append({
                                "row": index + 2,
                                "field": error["field"],
                                "error": error["error"]
                            })
                        continue

                    package_id = packages.get(amperage)
                    area_id = areas.get(area)

                    try:
                        customer_data = MeterFileUploadRow(
                            customer_full_name=customer_full_name,
                            customer_phone_number=customer_phone_number,
                            address=address,
                            area_id=area_id,
                            package_id=package_id,
                            initial_reading=initial_reading,
                            package_type=package_type
                        )
                        validated_customers.append(customer_data)
                    
                    except Exception as pydantic_error:

                        if hasattr(pydantic_error, 'errors'):

                            for error in pydantic_error.errors():
                                field = ".".join(str(loc) for loc in error["loc"])
                                validation_errors.append({
                                    "row": index + 2,
                                    "field": field.replace('_', ' '),
                                    "error": error["msg"]
                                })
                        else:

                            validation_errors.append({
                                "row": index + 2,
                                "field": "general",
                                "error": str(pydantic_error)
                            })
                        continue

                except Exception as general_error:

                    logger.warning(f"Unexpected error in row {index + 2}: {general_error}")
                    validation_errors.append({
                        "row": index + 2,
                        "field": "general",
                        "error": str(general_error)
                    })
                    continue
            
            logger.info(f"Validated customers: {len(validated_customers)}")
            logger.info(f"Validation errors: {len(validation_errors)}")

            if validation_errors:
                logger.warning(f"Found {len(validation_errors)} validation errors")
                raise ValidationError(
                    message="Validation errors found in the CSV file",
                    errors=validation_errors
                )
            

            result = {
                "valid_meters": [meter.model_dump() for meter in validated_customers],
                "validation_errors": validation_errors,
                "summary": {
                    "total_rows": len(meters_df),
                    "valid_count": len(validated_customers),
                    "invalid_count": len(validation_errors)
                }
            }

            return result

        except (
            InvalidColumnsException,
            InvalidPackageError,
            ValidationError
        ):
            raise


        except Exception as e:
            logger.error(f"Error in process_customers_csv: {e}")
            raise e
        

    async def upload_meters(self, request: Request, file:Optional[UploadFile], session: AsyncSession):
        """
        Upload meters from a file.
        """
        try:
            await FileValidator.validate_file(
                file=file,
                **FileValidationConfigs.SPREADSHEETS,  
                require_file=True
            )

            packages, areas, customers = await asyncio.gather(
                self.meters_queries.get_all_packages_query(
                    session=session
                ),
                self.meters_queries.get_all_areas_query(
                    session=session
                ),
                self.meters_queries.get_all_customers_names_phone_and_addresses_query(
                    session=session
                )
            )

            file_content = await file.read()
            if file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                file_type = "EXCEL"
            elif file.content_type == "text/csv":
                file_type = "CSV"

            try:
                results = await asyncio.wait_for(
                asyncio.to_thread(
                    self.process_customers_file,
                    file_content,
                    packages,
                    areas,
                    customers,
                    file_type
                ),
                timeout=300  # 5 minutes timeout
            )
            except asyncio.TimeoutError:
                raise FileProcessingTimeoutException(
                    timeout=300
                )
            
            token = request.state.user
            query_results = await self.meters_queries.insert_meters_from_file_query(
                meters_data=results.get("valid_meters"),
                created_by=token.get("user_id"),
                session=session
            )

            return success_response(
                message="Meters uploaded successfully",
                data=query_results
            )

        except (
            ValidationError,
            InvalidColumnsException,
            InvalidPackageError,
            EmptyFileException,
            FileProcessingTimeoutException,
            InvalidAreaNameException
            ):
            raise

        except Exception as e:
            logger.error(f"Error in upload_meters: {str(e)}")
            raise InternalServerError(
                message="An error occurred while uploading meters",
            )




   