# УЧЕБНЫЙ ПРОЕКТ FOODGRAM

## Презентация

**Foodgram** - это SPA приложение, являющееся платформой для публикации рецептов пользователями. В проекте каждый пользователь может добавить себе аватар, добавить рецепты в избранное и составить и скачать корзину с покупками. У каждого рецепта на платформе есть название, список ингредиентов, время приготовления, подробное описание и изображение конечного продукта.

## Развертывание проекта

### Локальный запуск (только API сервис)

#### Скопируйте репозиторий на свой персональный компьютер:
 
```
git clone https://github.com/Ivisa1/foodgram-st
```
Перейдите в папку проекта командой:
```
cd foodgram_st
```

#### Создайте виртуальное окружение и активируйте его:

```
python -m venv venv
.\venv\Scripts\activate
```
(Windows PowerShell) \
\
или
```
python -m venv venv
source venv/bin/activate
```
(Linux Bash)

#### Установите зависимости из файла:

```
pip install -r backend\foodgram_api\requirements.txt
```

#### В папке infra создайте файл .env по образцу .example_env

#### Выполните миграции, импорт тестовых данных и коллекцию статики (находясь в корневой папке):

```
python backend/foodgram_api/manage.py migrate
python backend/foodgram_api/manage.py loaddata backend/data/initial_data.json
python backend/foodgram_api/manage.py collectstatic --noinput
```

#### Запустите сервер:

```
python backend/foodgram_api/manage.py runserver
```

### Полноценный запуск

#### В файле infra/.env установите значение SQLITE на False

#### Перейдите в папку infra и запустите контейнеры:

```
cd infra
docker compose up -d --build
```

#### Выполните миграции, импорт тестовых данных и коллекцию статики:

```
docker compose exec backend python foodgram_api/manage.py migrate
docker compose exec backend python foodgram_api/manage.py loaddata data/initial_data.json
docker compose exec backend python foodgram_api/manage.py collectstatic --noinput
```