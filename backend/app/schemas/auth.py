from pydantic import BaseModel, Field, EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")


class MagicLinkResponse(BaseModel):
    status: str = Field(..., description="The status of the magic link request")


class VerifyRequest(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")
    token: str = Field(..., description="The OTP/token received by the user")


class VerifyResponse(BaseModel):
    access_token: str = Field(..., description="The access token for auth")
