# «Фудграм» - сервис для публикации рецептов

**«Фудграм»** — сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок» - он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Сервис доступен по адресу:

```
http://13.250.250.250/
```
# Доступ к админке:
login - ua-wef@mail.ru pass - 000111

# Запуск проекта на сервере:
Для работы сервиса на сервере должны быть установлены **Docker** и **docker-compose**

Клонируйте репозиторий командой:
```
git clone git@github.com:VK73-dev/foodgram-project-react.git
```

Перейдите в каталог:
```
cd foodgram-project-react/infra/
```

Выполните команду для запуска контейнера:
```
docker compose up
```

Выполните миграции:
```
docker-compose exec backend python manage.py makemigrations

docker-compose exec backend python manage.py migrate
```

Команда для сбора статики:
```
docker-compose exec backend python manage.py collectstatic
```

Команда для создания суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```

Команда для подгрузки ингредиентов:
```
docker compose exec backend python manage.py loadmodels --path recipes/data/ingredients.json
```

## Примеры запросов к API:
Список рецептов: [GET /api/recipes/](http://127.0.0.1/api/recipes/)

Получение рецепта: [GET /api/recipes/{id}/](http://127.0.0.1/api/recipes/{id}/)

Создание рецепта: [POST /api/recipes/](http://127.0.0.1/api/recipes/)
```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

Список ингредиентов: [GET /api/ingredients/](http://127.0.0.1/api/ingredients/)

Получение ингредиента: [GET /api/ingredients/{id}/](http://127.0.0.1/api/ingredients/{id}/)

Cписок тегов: [GET /api/tags/](http://127.0.0.1/api/tags/)

Получение тега: [GET /api/tags/{id}/](http://127.0.0.1/api/tags/{id}/)

## Использованные технологии:
* Python
* Django ORM
* REST API
* DRF
* Docker
* postgresql
* nginx
* gunicorn

## Автор:
**[Viacheslav Korablev](https://github.com/VK73-dev/)**
