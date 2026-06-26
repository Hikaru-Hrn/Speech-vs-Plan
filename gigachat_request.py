import requests
from get_access_token import get_access_token
import json

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

def main():
    file_path = 'src/lectures/lecture_3.txt'
    transcribe_file_path = 'src/transcripts/lecture_3_transcript.txt'
    
    print(f"Анализируем файл: {file_path}")
    
    response = ask_with_file_content(file_path, transcribe_file_path)
    
    print(f"\nСтатус ответа: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*60)
        print("ВЫЖИМКА ОТ GIGACHAT:")
        print("="*60)
        
        content = result['choices'][0]['message']['content']
        print(content)
        
        output_file = 'summary_result.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n Результат сохранен в файл: {output_file}")
    else:
        print(f"Ошибка: {response.status_code}")
        print("Текст ошибки:")
        print(response.text)

if __name__ == "__main__":
    main()