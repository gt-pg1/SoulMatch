# SoulMatch


## Описание

Проект представляет собой веб-сервис, реализованный с использованием Django и Django Rest Framework, который имитирует основные компоненты системы поиска новых знакомств на основе жизненных приоритетов пользователей.

## Установка и запуск проекта

### Требования

-   Python
-   Docker
-   docker-compose

### Запуск

1.  Склонируйте репозиторий проекта:

```bash
git clone https://github.com/gt-pg1/SoulMatch
```
```bash
cd SoulMatcher
```  
2.  Запустите проект с помощью Docker Compose:
 
```bash
 docker-compose up
```  
        После выполнения этой команды подождите около 10 минут, пока происходит импорт данных из файла `participants.jsonl`.
    
3.  После успешного запуска проекта, вы можете получить доступ к панели администратора по адресу:

`http://0.0.0.0:8000/admin/` 

Доступ к панели администратора:

-   Логин: `admin`
-   Пароль: `adminpass`

## Работа с API

Проект предоставляет RESTful API с следующими эндпоинтами:

1.  `/api/soulmate/register/` - регистрация нового пользователя.
    
Пример с использованием `curl`:

```bash
curl -X POST http://0.0.0.0:8000/api/soulmate/register/ -d "username=john_doe&email=john.doe@example.com&password=mysecurepassword"
```
    
Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/register/`
-   Method: POST
-   Body: x-www-form-urlencoded
    -   Key: `username`, Value: `john_doe`
    -   Key: `email`, Value: `john.doe@example.com`
    -   Key: `password`, Value: `mysecurepassword`

            После регистрации в консоли отобразится письмо с ссылкой, подтверждающей почту.

2.  `/api/soulmate/email-confirmation/<str:token>/` - подтверждение email.

Пример с использованием `curl`:

```bash
curl -X POST http://0.0.0.0:8000/api/soulmate/email-confirmation/your_email_token_here
```

Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/email-confirmation/your_email_token_here`
-   Method: POST
3.  `/api/soulmate/token/` - получение токена доступа.
    
Пример с использованием `curl`:
    
```bash
curl -X POST http://0.0.0.0:8000/api/soulmate/token/ -d "username=john_doe&password=mysecurepassword"
```
    
Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/token/`
-   Method: POST
-   Body: x-www-form-urlencoded
    -   Key: `username`, Value: `john_doe`
    -   Key: `password`, Value: `mysecurepassword`

4. `/api/soulmate/temp_protected_view/` - Проверка работы токена:

Пример с использованием `curl`:
```bash
curl -X GET http://0.0.0.0:8000/api/soulmate/temp_protected_view/ -H "Authorization: Bearer your_token_here"
```
Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/temp_protected_view/`
-   Method: GET
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

### Работа с приоритетами (CRUD операции):

Эндпоинт: `/api/priorities/`

**1. GET** - получение списка приоритетов.

Пример с использованием `curl`:

```bash
curl -X GET http://0.0.0.0:8000/api/soulmate/priorities/ -H "Authorization: Bearer your_token_here" 
```
Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/priorities/`
-   Method: GET
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

**2. POST** - создание нового приоритета.

Пример с использованием `curl`:

```bash
curl -X POST http://0.0.0.0:8000/api/soulmate/priorities/ -d "aspect=some_aspect&attitude=positive&weight=5" -H "Authorization: Bearer your_token_here" 
```
Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/priorities/`
-   Method: POST
-   Body: x-www-form-urlencoded
    -   Key: `aspect`, Value: `some_aspect`
    -   Key: `attitude`, Value: `positive`
    -   Key: `weight`, Value: `5`
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

**3. PUT** - полное обновление приоритета.

Пример с использованием `curl`:

```bash
curl -X PUT http://0.0.0.0:8000/api/soulmate/priorities/1/ -d "aspect=new_aspect&attitude=negative&weight=7" -H "Authorization: Bearer your_token_here"
``` 

Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/priorities/1/`
-   Method: PUT
-   Body: x-www-form-urlencoded
    -   Key: `aspect`, Value: `new_aspect`
    -   Key: `attitude`, Value: `negative`
    -   Key: `weight`, Value: `7`
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

**4. PATCH** - частичное обновление приоритета.

Пример с использованием `curl`:

```bash
curl -X PATCH http://0.0.0.0:8000/api/soulmate/priorities/1/ -d "weight=8" -H "Authorization: Bearer your_token_here"
```

Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/priorities/1/`
-   Method: PATCH
-   Body: x-www-form-urlencoded
    -   Key: `weight`, Value: `8`
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

**5. DELETE** - удаление приоритета.

Пример с использованием `curl`:

```bash
curl -X DELETE http://0.0.0.0:8000/api/soulmate/priorities/1/ -H "Authorization: Bearer your_token_here" 
```

Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/priorities/1/`
-   Method: DELETE
-   Headers: Key: `Authorization`, Value: `Bearer your_token_here`

## Запуск тестов
```bash
docker-compose exec web python SoulMatcher/manage.py test soulmate.tests
``` 


## Алгоритм сравнения совместимости


Алгоритм сравнения совместимости пользователей реализован в представлении `CompatibleUsersView`. Алгоритм вычисляет совместимость на основе косинусного сходства между векторами приоритетов пользователей.

1.  Сначала получается вектор приоритетов для заданного пользователя с помощью метода `get_user_vector`.
    
2.  Затем для заданного пользователя ищутся другие пользователи, у которых есть общие приоритеты.
    
3.  Вычисляется степень совместимости на основе косинусного сходства между их векторами приоритетов. Векторы представляют собой списки чисел, где положительные значения указывают на положительное отношение к аспекту, а отрицательные - на отрицательное.
    
4.  Результаты сортируются по убыванию степени совместимости и возвращаются через API.
    
**Авторизация для этого представления не была добавлена специально, для удобства тестирования.**

Подробности реализации в коде класса `CompatibleUsersView`.

**Пример запроса** для получения списка совместимых пользователей с использованием `curl`:

```bash
curl -X GET http://0.0.0.0:8000/api/soulmate/compatible-users/10/ 
```

Пример конфигурации для Postman:

-   URL: `http://0.0.0.0:8000/api/soulmate/compatible-users/10/`
-   Method: GET

В админке, в карточке пользователя, вы можете увидеть все привязанные к нему приоритеты. Чтобы перейти к определенному пользователю, можно использовать его ID, добавив его к URL в следующем формате: `http://0.0.0.0:8000/admin/soulmate/customuser/{id}`, где `{id}` - это идентификатор пользователя.

## Email рассылка

```bash
docker-compose exec web python SoulMatcher/manage.py send_emails 
```

## Проверка кэширования
```bash
docker-compose exec web /bin/bash
```
```bash
cd /app/SoulMatcher/soulmate/cache
```
```bash
ls
```