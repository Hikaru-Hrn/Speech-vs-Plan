import requests
import uuid
import json
import os
import time

GET_TOKEN_PARAMS_FILE = 'get_access_token.json'
SAVE_TOKEN_FILE = 'access_token.json'

def _form_request():
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


def get_access_token():
    if not os.path.exists(SAVE_TOKEN_FILE) or os.path.getsize(SAVE_TOKEN_FILE) == 0:
        response_json = _form_request()
        return response_json if response_json else None
    with open(SAVE_TOKEN_FILE, 'r') as acj:
        data = json.load(acj)
    if data['expires_at'] > int(time.time() * 1000):
        return data
    else:
        return response_json if response_json else None


BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
access_token_json = get_access_token()


def ask_with_file_content(lecture_file_path: str, transcribe_file_path: str):
    """Читает файл и отправляет его содержимое напрямую в запросе"""
    with open('prompts/compare_plan.md', 'r', encoding='utf-8') as compare_prompt:
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
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    print(f"Размер текста: {len(file_content)} символов")
    
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        verify=False
    )
    
    return response