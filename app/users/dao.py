from app.dao.base import BaseDAO
from app.users.models import Users
from app.database import async_session_maker
from sqlalchemy import select

class UsersDAO(BaseDAO):
    model = Users

    @staticmethod
    async def find_one_or_none(**filter_by):
        async with async_session_maker() as session:
            query = select(Users).filter_by(**filter_by)
            result = await session.execute(query)
            user = result.scalars().first()
            return user
    
    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=model_id)
            result = await session.execute(query)

            return result.scalars().first()