from pydantic import BaseModel, ConfigDict, EmailStr, Field

from enums import Roles


class UserBase(BaseModel):
    first_name: str = Field(max_length=50, examples=["Ali"])
    last_name: str = Field(max_length=50, examples=["Valiyev"])
    email: EmailStr = Field(max_length=100, examples=["ali.valiyev@example.com"])


class UserCreate(UserBase):
    username: str = Field(min_length=3, max_length=50, examples=["AliValiyev"])
    password: str = Field(min_length=6, max_length=100, examples=["securepassword"])


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Roles | None = Field(default=Roles.USER, examples=["user", "admin"])
    user_avatar: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
