from pydantic import BaseModel, EmailStr, Field


class AdminBootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=120)
    bootstrap_token: str | None = Field(default=None, max_length=200)


class AdminBootstrapOut(BaseModel):
    user_id: str
    email: EmailStr
    role: str
    message: str


class AdminForgotPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
    email: EmailStr | None = None


class AdminForgotPasswordOut(BaseModel):
    user_id: str
    email: EmailStr
    message: str