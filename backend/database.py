from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Probably remove echo in prod. Neon requires ssl - this should be the correct way to do it for asyncpg.
# Pscs=0 is to tell asynpc to send raw query every time, don't try to remember and name specific queries
engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"ssl": True, "prepared_statement_cache_size": 0})

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)   # sessionmaker is a factory object that produces new AsyncSessions on demand


async def init_db():    # Sets up the connection pool I think
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():    # this isn't used on its own. Its also not called by the user. This is passed into the Depends
    async with async_session() as session:
        yield session