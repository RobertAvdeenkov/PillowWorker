from fastapi import HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import select
from database import SessionLocal
from models import User
import os
from datetime import datetime

SECRET=os.getenv('SECRET','a')
ALGORITHM=os.getenv('ALGORITHM','HS256')

def create_token(user:str, timedelta):
    payload={
        'sub':user,
        'exp':datetime.now()+timedelta
    }
    return jwt.encode(payload,SECRET,ALGORITHM)

async def get_user(token:str):
    try:
        name=jwt.decode(token,SECRET,algorithms=[ALGORITHM])['sub']
    except ExpiredSignatureError:
        raise HTTPException(401,'Токен протух!')
    except JWTError:
        raise HTTPException(401,'Неправильный токен!')
    
    async with SessionLocal() as db: #type:ignore
        result=(await db.execute(select(User).filter(User.name==name))).first()
        if not result:
            raise HTTPException(404,'Такого пользователя нет!')
        return result[0]