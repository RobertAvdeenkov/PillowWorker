import aio_pika as pika
import json
import asyncio
import os
from storage import BUCKET, client
from PIL import Image,ImageFilter
from models import ReferenceImage
import io
import uuid
from database import SessionLocal
from fastapi import FastAPI
from logger import logger
from sqlalchemy import text

app=FastAPI()

background_tasks = set()

def spawn(coro):
    t = asyncio.create_task(coro)
    background_tasks.add(t)
    t.add_done_callback(background_tasks.discard)
    return t

def apply_filter(img, filter_name: str):
    if filter_name == 'grayscale':
        return img.convert('L')
    elif filter_name == 'blur':
        return img.filter(ImageFilter.BLUR)
    elif filter_name == 'sharpen':
        return img.filter(ImageFilter.SHARPEN)
    return img

async def main():
    connection=await pika.connect_robust(os.getenv('RABBITMQ_URL',None))
    channel=await connection.channel()
    queue=await channel.declare_queue('images_queue')
    await channel.declare_queue('retry', durable=True, arguments={'x-message-ttl':30000, 'x-dead-letter-routing-key':'images_queue', 'x-dead-letter-exchange':''})

    async def callback(message:pika.IncomingMessage):
        async with message.process():
            body=json.loads(message.body.decode())
            try:
                response=client.get_object(BUCKET, object_name=body['name'])
                try:
                    image_data=response.read()
                finally:
                    response.close()
                    response.release_conn()

                img=Image.open(io.BytesIO(image_data))
                new_image=apply_filter(img, body['filter'])

                new_filename=f'{uuid.uuid4()}.jpg'

                image_bytes=io.BytesIO()
                new_image.save(image_bytes, format='JPEG')
                image_bytes.seek(0)

                client.put_object(BUCKET, new_filename, image_bytes, len(image_bytes.getvalue()), content_type='image/jpeg')
                img.close()

                async with SessionLocal() as db: #type:ignore
                    target=ReferenceImage(size=len(image_bytes.getvalue()), image_id=body['id'], user_id=body['user_id'], url=new_filename)
                    db.add(target)
                    await db.execute(text('UPDATE images SET status=\'done\' WHERE id=:image_id'), {'image_id':body['id']})
                    await db.commit()
            except Exception as e:
                logger.error(f'ERROR: {e}')
                await channel.default_exchange.publish(routing_key='retry', message=pika.Message(json.dumps(body).encode()))

    await queue.consume(callback) #type:ignore
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        return

@app.on_event('startup')
async def startup():
    logger.info('Main Worker Started')
    spawn(main())

@app.get('/')
async def root():
    return {'status':'ok'}



