from typing import Generic, Type, TypeVar

from app.dao.database import Base
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import func
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

T = TypeVar('T', bound=Base)


class BaseDAO(Generic[T]):
    model: Type[T] = None

    def __init__(self, session: AsyncSession):
        self._session = session
        if self.model is None:
            raise ValueError('Model should be determined')

    async def find_one_or_none_by_id(self, data_id: int):
        try:
            query = select(self.model).filter_by(id=data_id)
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()
            log_message = (
                f"Запись {self.model.__name__} с ID {data_id} "
                f"{'найдена' if record else 'не найдена'}."
            )
            logger.info(log_message)
            return record
        except SQLAlchemyError as e:
            logger.error(f'Error searching record with ID {data_id}: {e}')
            raise
