# Create a new file: globals/utils/fileValidator.py
from typing import Optional, List
from fastapi import UploadFile
from globals.exceptions.global_exceptions import ValidationError
from globals.utils.logger import logger

class FileValidator:
    @staticmethod
    async def validate_file(
        file: Optional[UploadFile],
        allowed_content_types: List[str],
        max_file_size: int,
        allowed_extensions: Optional[List[str]] = None,
        require_file: bool = True
    ) -> bool:
        """
        Validate uploaded file with comprehensive checks.
        
        Args:
            file: The uploaded file
            allowed_content_types: List of allowed MIME types
            max_file_size: Maximum file size in bytes
            allowed_extensions: List of allowed file extensions (optional)
            require_file: Whether file is required or optional
            
        Returns:
            bool: True if validation passes
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            if require_file and not file:
                logger.error("No file uploaded")
                raise ValidationError(
                    message="No file uploaded. Please select a file to upload.",
                    errors=[]
                )
            
            if not require_file and not file:
                return True
            
            if not file.filename:
                logger.error("No filename provided")
                raise ValidationError(
                    message="Invalid file. Please select a valid file to upload.",
                    errors=[]
                )
            
            if file.size is not None and file.size == 0:
                logger.error("Empty file uploaded")
                raise ValidationError(
                    message="Empty file uploaded. Please select a file with data.",
                    errors=[]
                )
            
            if file.size is not None and file.size > max_file_size:
                size_mb = round(file.size / (1024 * 1024), 2)
                max_size_mb = round(max_file_size / (1024 * 1024), 2)
                logger.error(f"File size exceeds limit: {size_mb}MB > {max_size_mb}MB")
                raise ValidationError(
                    message=f"File size exceeds the maximum limit of {max_size_mb} MB.",
                    errors=[]
                )
            
            if file.content_type not in allowed_content_types:
                logger.error(f"Invalid file type: {file.content_type}")
                raise ValidationError(
                    message="Invalid file type. Allowed types are: " + ", ".join(allowed_content_types),
                    errors=[]
                )
            
            if allowed_extensions:
                file_extension = file.filename.lower().split('.')[-1]
                if file_extension not in allowed_extensions:
                    logger.error(f"Invalid file extension: {file_extension}")
                    raise ValidationError(
                        message=f"Invalid file extension. Only {', '.join(allowed_extensions)} files are allowed.",
                        errors=[]
                    )
            
            try:
                file_contents = await file.read()
                if len(file_contents) == 0:
                    raise ValidationError(
                        message="File appears to be empty or corrupted.",
                        errors=[]
                    )

                await file.seek(0)
                
            except Exception as read_error:
                logger.error(f"Error reading file: {str(read_error)}")
                raise ValidationError(
                    message="Error reading file. Please ensure the file is not corrupted.",
                    errors=[str(read_error)]
                )
            
            logger.info(f"File validation passed: {file.filename}")
            return True
            
        except ValidationError:
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in file validation: {str(e)}")
            raise ValidationError(
                message="An error occurred while validating the file.",
                errors=[str(e)]
            )

    @staticmethod
    def get_file_info(file: UploadFile) -> dict:
        """Get file information for logging/debugging."""
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
            "size_mb": round(file.size / (1024 * 1024), 2) if file.size else None
        }


class FileValidationConfigs:

    IMAGES = {
        "allowed_content_types": ["image/jpeg"],
        "allowed_extensions": ["jpg", "jpeg"],
        "max_file_size": 5 * 1024 * 1024  # 5 MB
    }
    

    DOCUMENTS = {
        "allowed_content_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
        "allowed_extensions": ["pdf", "doc", "docx"],
        "max_file_size": 50 * 1024 * 1024  # 50 MB
    }
    

    SPREADSHEETS = {
        "allowed_content_types": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ],
        "allowed_extensions": ["csv", "xlsx", "xls"],
        "max_file_size": 20 * 1024 * 1024  # 20 MB
    }
    

    ARCHIVES = {
        "allowed_content_types": [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed"
        ],
        "allowed_extensions": ["zip", "rar", "7z"],
        "max_file_size": 100 * 1024 * 1024  # 100 MB
    }