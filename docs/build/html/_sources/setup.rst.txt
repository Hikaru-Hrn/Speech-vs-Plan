Настройка
---------

Для работы с GigaChat необходимо:

1. Получить авторизационные данные в личном кабинете GigaChat
2. Создать файл ``get_access_token.json`` со структурой:

.. code-block:: json

    {
        "url": "https://gigachat.devices.sberbank.ru/api/v1/oauth",
        "auth_data": "ваш_токен",
        "payload": "scope=GIGACHAT_API_PERS",
        "cert_path": "/путь/до/сертификата.pem"
    }