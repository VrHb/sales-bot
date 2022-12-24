# Бот для продаж 

Бот работает с помощью взамидействия с API cms системы [elasticpath](https://www.elasticpath.com/) и позволяет продавать товары.

## Как установить

### Настройка переменных окружения:

- Для хранения переменных окружения создаем файл .env:

```
touch .env
```

1. Токен telegram бота, получаем после регистрации [бота](https://habr.com/ru/post/262247/)

```
echo "TG_BOT_TOKEN='<токен tg бота>'" >> .env
```

2. Переменные для доступа к API ElasticPath, как получить читаем [тут](https://documentation.elasticpath.com/commerce-cloud/docs/developer/get-started/your-first-api-request.html)

```
echo "MOLTIN_CLIENT_ID='<id клиента>'" >> .env
```
```
echo "MOLTIN_CLIENT_SECRET='<секретный ключ клиента>'" >> .env
```

3. Параметры для подключения к вашей db redis, смотрим [доку](https://redis.com/redis-enterprise-cloud/overview/) 

```
echo "REDIS_DB='<адрес db>'\nREDIS_PORT='<порт db>'\nREDIS_PASSWORD='<пароль для подключения>'" >> .env
```

### Установка:

- Необходимо установить интерпретатор python **не выше** версии 3.8
- Cкопировать содержимое проекта к себе в рабочую директорию
- Активировать внутри рабочей директории виртуальное окружение:

```
python -m venv [название окружения]
```

- Установить зависимости(необходимые библиотеки):

```
pip install -r requirements.txt
```

### Как пользоваться:

- Запускаем telegram бота:

```
python tg_bot.py
```
