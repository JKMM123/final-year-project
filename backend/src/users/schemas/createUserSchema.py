from pydantic import BaseModel, Field, field_validator
import re



from enum import Enum

class UserRole(str, Enum):
    system = "system"
    admin = "admin"
    user = "user"

    @classmethod
    def can_create_role(cls, creator_role: str, target_role: str) -> bool:
        creator_role = creator_role.lower().strip()
        target_role = target_role.lower().strip()
        permissions = {
            cls.system.value: [cls.admin.value, cls.user.value],
            cls.admin.value: [cls.user.value],
            cls.user.value: []
        }
        return target_role in permissions.get(creator_role, [])

    @classmethod
    def can_delete_role(cls, deleter_role: str, target_role: str) -> bool:
        deleter_role = deleter_role.lower().strip()
        target_role = target_role.lower().strip()
        permissions = {
            cls.system.value: [cls.admin.value, cls.user.value],
            cls.admin.value: [cls.user.value],
            cls.user.value: []
        }
        return target_role in permissions.get(deleter_role, [])
    
    @classmethod
    def can_update_role(cls, updater_role: str, target_role: str) -> bool:
        updater_role = updater_role.lower().strip()
        target_role = target_role.lower().strip()
        permissions = {
            cls.system.value: [cls.admin.value, cls.user.value],
            cls.admin.value: [cls.user.value],
            cls.user.value: []
        }
        return target_role in permissions.get(updater_role, [])




class CreateUserRequestBody(BaseModel):
    username: str = Field(..., description="The username of the user")
    phone_number: str = Field(..., description="The phone number of the user")
    role: str = Field(..., description="The role of the user, e.g., 'admin', 'user'")

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v

    @field_validator("role")
    def validate_role(cls, v):
        if v not in ["system", "admin", "user"]:
            raise ValueError("Invalid role. Role must be either 'system', 'admin' or 'user'.")
        return v
    
    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid username format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v
    

    class Config:
        extra = "forbid"
