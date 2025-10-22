"""Password-related Pydantic schemas"""

from pydantic import BaseModel, Field


class SetPasswordRequest(BaseModel):
    """Schema for setting password for OAuth users"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirm_password: str = Field(..., description="Password confirmation")
    
    def validate_passwords_match(self):
        """Validate that passwords match"""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class SetPasswordResponse(BaseModel):
    """Schema for set password response"""
    message: str