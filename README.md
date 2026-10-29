<div align="center">

# Севрис для обработки изображений

### Стек

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![MinIO](https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white)](https://min.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)

</div>

---

### Как работает
В проекте учатсвуют кеширование и 3 воркера.
Пользователь прикрепляет фотографию, **основной воркер** пытается её обработать, если все получилось, то статус загруженной картинки заменяется на **'done'** вместо **'pending'** и на главной можно увидеть референс. Если обработка не прошла успешно, то **retry** 3 раза её проверяет. В случае неудачи в дело вступает **DLX** воркер, который меняет статус картинки на **'failed'**.


<div align="center">
