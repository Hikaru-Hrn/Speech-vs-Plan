Использование
=============

Основные функции
----------------

Функция ``get_access_token()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Получение токена доступа для работы с GigaChat API:

.. code-block:: python

    from analyze import get_access_token
    
    token_data = get_access_token()
    print(token_data['access_token'])

Функция ``ask_with_file_content()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Сравнение плана лекции с транскрибацией выступления:

.. code-block:: python

    from analyze import ask_with_file_content
    
    response = ask_with_file_content(
        lecture_file_path='plan.txt',
        transcribe_file_path='speech.txt'
    )
    print(response.json())

Пример полного скрипта
----------------------

.. code-block:: python

    from analyze import ask_with_file_content
    
    # Пути к файлам
    lecture = 'lecture_plan.txt'
    transcribe = 'transcribe.txt'
    
    # Отправка запроса к GigaChat
    result = ask_with_file_content(lecture, transcribe)
    
    if result.status_code == 200:
        print("Анализ выполнен успешно")
        print(result.json()['choices'][0]['message']['content'])
    else:
        print(f"Ошибка: {result.status_code}")
        print(result.text)