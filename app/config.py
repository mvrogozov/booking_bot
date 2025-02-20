import os
from urllib.parse import quote

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from faststream.rabbit import RabbitBroker
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    BOT_TOKEN: str
    ADMIN_IDS: list[int]
    INIT_DB: bool
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_URL: str = f'sqlite+aiosqlite:///{BASE_DIR}/data/db.sqlite3'
    STORE_URL: str = f'sqlite:///{BASE_DIR}/data/jobs.sqlite'
    TABLES_JSON: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dao", "tables.json")
    SLOTS_JSON: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dao", "slots.json")

    BASE_URL: str
    RABBITMQ_USERNAME: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    VHOST: str

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USERNAME}:{quote(self.RABBITMQ_PASSWORD)}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.VHOST}"
        )

    @property
    def hook_url(self) -> str:
        return f'{self.BASE_URL}/webhook'

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '.env'
        )
    )


settings = Settings()

log_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "log.txt"
)
logger.add(
    log_file_path,
    format=settings.FORMAT_LOG,
    level="INFO",
    rotation=settings.LOG_ROTATION
)
broker = RabbitBroker(url=settings.rabbitmq_url)
scheduler = AsyncIOScheduler(
    jobstores={'default': SQLAlchemyJobStore(url=settings.STORE_URL)}
)
