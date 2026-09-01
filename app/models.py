from pydantic import BaseModel, EmailStr, validator

class RegisterRequest(BaseModel):
    email: EmailStr
    plan: str  # "Free", "Pro", "Enterprise"
    @validator("plan")
    def validate_plan(cls, v):
        if v not in ["Free", "Pro", "Enterprise"]:
            raise ValueError("Plan must be 'Free', 'Pro', or 'Enterprise'")
        return v
class RegisterResponse(BaseModel):
    api_key: str
    plan: str
    expires_in_days: int
    message: str