import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine

engine=create_async_engine(os.getenv('DATABASE_URL','sqlite+aiosqlite:///images.db'))
SessionLocal=sessionmaker(bind=engine,class_=AsyncSession,expire_on_commit=False) #type:ignore

async def get_db():
    async with SessionLocal() as db: #type:ignore
        try:
            yield db
        finally:
            await db.close()