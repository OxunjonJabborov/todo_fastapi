from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import DATABASE_URL, DB_ECHO

connect_args = {'check_same_thread': False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=DB_ECHO)

async_session = async_sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
