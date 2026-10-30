<div align="center">

# Сервис для обработки изображений

Ссылка: https://pillowworker.onrender.com/

### Стек

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![MinIO](https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white)](https://min.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![bcrypt](https://img.shields.io/badge/bcrypt-003A70?style=for-the-badge&logo=letsencrypt&logoColor=white)](https://github.com/pyca/bcrypt)
</div>

---

### Как работает

В проекте участвуют кеширование, 3 воркера и S3.
Пользователь прикрепляет фотографию, **основной воркер** пытается её обработать, если все получилось, то статус загруженной картинки заменяется на **'done'**, вместо **'pending'** и на главной можно увидеть референс. Если обработка не прошла успешно, то **retry** 3 раза её проверяет. В случае неудачи в дело вступает **DLX** воркер, который меняет статус картинки на **'failed'**. Обработка представляет из себя наложение фильтров Pillow, хотя можно загрузить изображение из без него.
Также есть ТГ бот. Там есть функции логина, выхода из аккаунта и наложение фильтра на фотографию. Пользователь отправляет файл с прикрепленным названием фильтра, а бот в свою очередь, отправляет сообщение в очередь вместе со всеми. К сообщению именно от ТГ добавляется новый ключ tg_id, по нему воркер понимает, куда отправить обработанный файл.

---

## Запуск

1. Скачайте файлы
2. Перейдите в папку и откройте терминал
3. Введите: docker-compose up --build


<div align="center">
