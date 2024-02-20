# Foodgram - сервис для хранения рецептов.
**https://foodgramstudy.hopto.org**

**Фудграм** — сайт, на котором можно регистрироваться, публиковать рецепты,
добавлять рецепты в избранное и подписываться на публикации других авторов.
Также доступен сервис «Список покупок».
Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

**Используемые технологии**

+ backend-часть проекта разработна на **Django REST framework**;
+ аутенфикация настроена с помощью **Djoser + SimpleJWT**;
+ frontend-часть разработана на **React**;
+ проект запущен на виртуальном удалённом сервере с помощью программы **Docker** с использованием:
  + **nginx** - настроена раздача статики, запросы с фронтенда переадресуются в контейнер с Gunicorn.
  + базы данных **PostgreSQL**
+ Проект оптимизируется и изменения заливаются автоматически с помощью сервиса **GitHub Actions**. При пуше в ветку master проект тестируется, в случае успешного прохождения тестов образы обновляются на **Docker Hub** и на сервере перезапускаются контейнеры из обновлённых образов.

**Развертывание проекта с помощью Docker**

1. Установите Docker
Полезные ссылки:
Для Windows:

https://learn.microsoft.com/ru-ru/windows/wsl/install
https://www.docker.com/products/docker-desktop/

Для Linux

https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script

Запустите сервис.
3. Склонируйте репозиторий.
```
git clone git@github.com:lengenkon/foodgram-project-react.git
```
3. Запустите проект
```
sudo docker compose up
```
4. Выполните миграции
```
sudo docker compose exec backend python manage.py migrate
```
5. Соберите статические файлы бэкэнда.
```
sudo docker compose exec backend python manage.py collectstatic --no-input
```
6. Создайте суперпользователя.
```
sudo docker compose exec backend python manage.py createsuperuser
```
7. Загрузите данные.
```
sudo docker compose exec backend python manage.py load_data_from_csv --file_name ingredients.csv --model_name Ingredient --app_name recipes
```
```
sudo docker compose exec backend python manage.py load_data_from_csv --file_name tags.csv --model_name Tag --app_name recipes
```

**Документация API**

В папке infra выполните:
```
docker compose up
```
Документация доступна по адресу: http://localhost/api/docs/

**Примеры запросов и ответов**

+ `GET api/recipes/{recipes_id}/` - адрес для GET, PATCH и DELETE-запросов для, соответственно, получения, частичного редактирования и удаления рецепта;
  + Пример ответа:
  ```
  {
    "id": 0,
    "tags": [
      {
        "id": 0,
        "name": "Завтрак",
        "color": "#E26C2D",
        "slug": "breakfast"
      }
    ],
    "author": {
      "email": "user@example.com",
      "id": 0,
      "username": "string",
      "first_name": "Вася",
      "last_name": "Пупкин",
      "is_subscribed": false
    },
    "ingredients": [
      {
        "id": 0,
        "name": "Картофель отварной",
        "measurement_unit": "г",
        "amount": 1
      }
    ],
    "is_favorited": true,
    "is_in_shopping_cart": true,
    "name": "string",
    "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
    "text": "string",
    "cooking_time": 1
  }
  ```
+ `POST api/recipes/` - адрес для POST-запроса для создания нового рецепта;
+ `GET api/recipes/` - адрес для получения списка рецептов.
+ `POST api/auth/token/` - адрес для получение токена
  + Пример запроса:
  ```
  {
      "username": "string",
      "password": "string"
  }
  ```
  + Пример ответа:
  ```
  {
      "token": "string"
  }
  ```

**Автор**

https://github.com/lengenkon
