```text
PillowWorker/
│   .gitignore
│   auth.py - JWT, bcrypt, регистрация, логин
│   bot.py - ТГ бот
│   database.py - подключение к БД, сессии
│   DLX_worker.py - DLX 
│   docker-compose.yml - описание сервисов
│   Dockerfile - сборка образа
│   logger.py - логирование
│   main.py - запуск сайт, CORS, роутеры
│   models.py - модели БД
│   pytest.ini - настройка тестов
│   README.md - документация
│   requirements.txt - необходимые библиотеки
│   retry_worker.py - retry воркер
│   storage.py - подключение к bucket
│   tasks.py - эндпоинты
│   worker.py - основной воркер
│
├───.github
│   └───workflows
│           test.yml - пайплайны
├───templates/
├───tests
│   │   load_testing.py - нагрузочное тестирование
│   └───test_pillow.py - pytest тестирование
```