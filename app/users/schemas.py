from pydantic import BaseModel, EmailStr


class SUserAuth(BaseModel):
    password: str
    email: EmailStr

    class Config:
        orm_mode = True
