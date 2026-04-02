from pydantic import BaseModel, Field, field_validator
from uuid import UUID
import re



# Define allowed placeholders - these will be replaced when sending messages
ALLOWED_PLACEHOLDERS = {
    # Customer data
    "{{customer_full_name}}", "{{customer_phone_number}}",
    "{{address}}", "{{area_name}}",
    
    # Bill data  
    "{{bill_amount}}", "{{due_date}}", "{{bill_month}}", "{{bill_year}}", 
    "{{payment_status}}", "{{days_overdue}}", "{{late_fee}}",
    
    # Meter data
    "{{meter_number}}", "{{current_reading}}", "{{previous_reading}}", 
    "{{package_type}}", "{{package_name}}",

}



class UpdateTemplateRequestPath(BaseModel):
    template_id: UUID = Field(..., description="Template ID")


class UpdateTemplateRequestBody(BaseModel):
    name: str = Field(..., description="Template name", max_length=255)
    message: str = Field(..., description="Template message with placeholders", max_length=1000)

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        
        # Allow Arabic, English, numbers, spaces, punctuation, and common symbols
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9\s.,!?_()-]+$", v):
            raise ValueError("Template name contains invalid characters")
        return v.strip()

    @field_validator("message")
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Template message cannot be empty")

        message = v.strip()
        
        # Extract all placeholders from the message using regex
        placeholder_pattern = r'\{\{[^}]+\}\}'
        found_placeholders = set(re.findall(placeholder_pattern, message))
        
        # Check for invalid placeholders
        invalid_placeholders = found_placeholders - ALLOWED_PLACEHOLDERS
        if invalid_placeholders:
            valid_list = ', '.join(sorted(ALLOWED_PLACEHOLDERS))
            invalid_list = ', '.join(sorted(invalid_placeholders))
            raise ValueError(
                f"Invalid placeholders found: {invalid_list}. "
                f"Allowed placeholders: {valid_list}"
            )
        
        # Validate message content (excluding placeholders for character validation)
        # Remove placeholders temporarily for content validation
        temp_message = re.sub(placeholder_pattern, '', message)
        if temp_message and not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9\s.,!?_()-]*$", temp_message):
            raise ValueError("Template message contains invalid characters (excluding valid placeholders)")
        
        return message

    class Config:
        extra = "forbid"
        str_strip_whitespace = True

