from sqlalchemy import Column,String,Integer,ForeignKey,Float,func,DateTime
from sqlalchemy.orm import DeclarativeBase,relationship

class Base(DeclarativeBase):pass

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    password=Column(String)
    refresh_token=Column(String,default='')
    tg_id=Column(String,default='')

    images=relationship('Image',back_populates='user')
    reference=relationship('ReferenceImage',back_populates='user')

class Image(Base):
    __tablename__='images'
    id=Column(Integer,primary_key=True)
    filename=Column(String)
    status=Column(String,default='pending')
    created_at=Column(DateTime,default=func.now())

    user_id=Column(Integer,ForeignKey('users.id'))
    user=relationship('User',back_populates='images')
    reference=relationship('ReferenceImage',back_populates='image', cascade="all, delete-orphan")

class ReferenceImage(Base):
    __tablename__='reference'
    id=Column(Integer,primary_key=True)
    size=Column(Float)
    url=Column(String)

    image_id=Column(Integer,ForeignKey('images.id'))
    user_id=Column(Integer,ForeignKey('users.id'))

    user=relationship('User',back_populates='reference')
    image=relationship('Image',back_populates='reference')