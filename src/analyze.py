import requests
import uuid
import json
import os
import time

GET_TOKEN_PARAMS_FILE = 'get_access_token.json'
SAVE_TOKEN_FILE = 'access_token.json'
BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

def _form_request() -> dict | None:
    """
    Выполнение API-запроса на получение токена доступа для GigaChat 
    и его сохранение в файл access_token.json

    :return: токен доступа, если операция успешна, иначе None
    :rtype: dict | None
    """
    rq_uid = str(uuid.uuid4())

    with open(GET_TOKEN_PARAMS_FILE, 'r') as data:
      params = json.load(data)

    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'RqUID': rq_uid,
      'Authorization': f'Bearer {params["auth_data"]}'
    }

    try:
        response = requests.request("POST", params['url'], 
                                    headers=headers, 
                                    data=params['payload'], 
                                    verify=params['cert_path'])
        response_json = response.json()
        with open(SAVE_TOKEN_FILE, 'w') as acj:
          json.dump(response_json, acj)
        return response_json
    except requests.exceptions.RequestException as re:
        print("Error: ", re)
        return None


def get_access_token() -> dict | None:
    """
    Получение токена доступа.
    Функция проверяет файл access_token.json

    Если файла access_token.json не существует или токен лоступа в нём устарел,
    вызывает _form_request()

    Если файл access_token.json существует и токен доступа в нем действителен,
    считывает токен из файла

    :return: токен доступа, если операция успешна, иначе None
    :rtype: dict | None
    """
    if not os.path.exists(SAVE_TOKEN_FILE) or os.path.getsize(SAVE_TOKEN_FILE) == 0:
        response_json = _form_request()
        return response_json if response_json else None
    with open(SAVE_TOKEN_FILE, 'r') as acj:
        data = json.load(acj)
    if data['expires_at'] > int(time.time() * 1000):
        return data
    else:
        response_json = _form_request()
        return response_json if response_json else None


def ask_with_file_content(lecture_file_path: str, transcribe_file_path: str) -> requests.Response:
    """
    Функция считывает содержимое двух файлов: 
    изначального плана лекции и транскрибации записи выступления преподавателя.
    Далее осуществляется API-запрос к LLM GigaChat с содержимым двух файлов для их сравнения

    :param lecture_file_path: Путь до файла с планом лекции
    :param transcribe_file_path: Путь до файла с транскрибацией выступления преподавателя
    :return: Ответ GigaChat
    :rtype: requests.Response
    """
    access_token_json = get_access_token()
    with open('../prompts/compare_plan.md', 'r', encoding='utf-8') as compare_prompt:
        compare_prompt_text = compare_prompt.read()
    with open(lecture_file_path, 'r', encoding='utf-8') as lf:
        file_content = lf.read()
    
    with open(transcribe_file_path, 'r', encoding='utf-8') as tf:
        transcribe_content = tf.read()
    max_chars = 35000
    if len(file_content) + len(transcribe_content) > max_chars:
        file_content = file_content[:max_chars] + "... (обрезано)"
    
    url = f"{BASE_URL}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token_json['access_token']}"
    }

    payload = {
        # "model": "GigaChat-2-Max",
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": f"""{compare_prompt_text}

                Текст плана лекции для анализа:
                    {file_content}

                То, что было сказано спикером фактически:
                    {transcribe_content}
                """
            }
        ],
        "temperature": 0.5,
        "max_tokens": 800
    }
    
    print(f"Размер текста: {len(file_content)} символов")
    
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        verify=False
    )
    
    return response