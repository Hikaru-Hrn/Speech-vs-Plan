# coding=utf8
import os
import time
import wave
import audioop
import grpc
import boto3

import urllib.request
import json

import yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
import yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc

from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = 4000
TARGET_SAMPLE_RATE = 16000


# Функция конвертации из WAV в идеальный RAW PCM
def convert_wav_to_pcm(wav_path, pcm_path):
    print(f"[КОНВЕРТЕР] Чтение файла {wav_path}...")
    try:
        with wave.open(wav_path, 'rb') as w:
            params = w.getparams()
            n_channels, sampwidth, framerate, n_frames = params[:4]

            # Читаем все сырые данные из WAV
            raw_data = w.readframes(n_frames)

            # 1. Если стерео — переводим в моно
            if n_channels > 1:
                raw_data = audioop.tomono(raw_data, sampwidth, 0.5, 0.5)

            # 2. Если разрядность не 16 бит (2 байта), приводим к 16 битам
            if sampwidth != 2:
                raw_data = audioop.lin2lin(raw_data, sampwidth, 2)

            # 3. Меняем частоту дискретизации на 16000 Гц
            if framerate != TARGET_SAMPLE_RATE:
                state = None
                raw_data, state = audioop.ratecv(
                    raw_data, 2, 1, framerate, TARGET_SAMPLE_RATE, state
                )

            # Сохраняем чистые байты
            with open(pcm_path, 'wb') as f:
                f.write(raw_data)

        print(f"[КОНВЕРТЕР] Успешно создан RAW PCM: {pcm_path}")
        return True
    except Exception as e:
        print(f"[КОНВЕРТЕР ОШИБКА] Не удалось обработать WAV: {e}")
        return False


# Функция загрузки файлов в Yandex Object Storage
def upload_to_bucket(local_file_path, bucket_name, object_name):
    print(f"[STORAGE] Загрузка {local_file_path} в публичный бакет...")
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        s3_client.upload_file(local_file_path, bucket_name, object_name)

        # Ссылка, так как бакет настроен публичным на чтение
        file_uri = f"https://storage.yandexcloud.net/{bucket_name}/{object_name}"
        print(f"[STORAGE] Файл доступен по ссылке: {file_uri}")
        return file_uri
    except Exception as e:
        print(f"[STORAGE ОШИБКА] Не удалось загрузить файл в бакет: {e}")
        return None


# Функция удаления временных файлов из бакета
def delete_from_bucket(bucket_name, object_name):
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        print(f"[STORAGE] Временный файл {object_name} успешно удален из бакета.")
    except Exception as e:
        print(f"[STORAGE ВАРНИНГ] Не удалось удалить файл из бакета: {e}")


# Функция отправки аудио и ожидания транскрибации через REST API
def run_async_grpc_stt(folder_id, iam_token, file_uri, api_key=None):
    cred = grpc.ssl_channel_credentials()
    stt_channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stt_stub = stt_service_pb2_grpc.SttServiceStub(stt_channel)

    specification = stt_service_pb2.RecognitionSpec(
        language_code='ru-RU',
        profanity_filter=True,
        model='general',
        audio_encoding='LINEAR16_PCM',
        sample_rate_hertz=TARGET_SAMPLE_RATE
    )
    recognition_config = stt_service_pb2.RecognitionConfig(specification=specification, folder_id=folder_id)
    audio = stt_service_pb2.RecognitionAudio(uri=file_uri)

    request = stt_service_pb2.LongRunningRecognitionRequest(config=recognition_config, audio=audio)

    if api_key:
        print("[STT] Авторизация через Сервисный аккаунт (API-ключ)...")
        metadata = (('authorization', f'Api-Key {api_key}'),)
    else:
        print("[STT] Авторизация через IAM-токен...")
        metadata = (('authorization', f'Bearer {iam_token}'),)

    try:
        print("[STT] Отправка запроса на асинхронное распознавание...")
        operation = stt_stub.LongRunningRecognize(request, metadata=metadata)
        operation_id = operation.id
        print(f"[STT] Создана фоновая операция. ID: {operation_id}")

        url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"

        while True:
            print("[STT] Файл обрабатывается в облаке, ожидание 5 секунд...")
            time.sleep(5)

            req = urllib.request.Request(url)
            if api_key:
                req.add_header('Authorization', f'Api-Key {api_key}')
            else:
                req.add_header('Authorization', f'Bearer {iam_token}')

            try:
                with urllib.request.urlopen(req) as resp:
                    op_data = json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                print(f"[ОШИБКА СЕТИ ПРИ ОПРОСЕ]: {e}")
                return None

            # Если задача завершена в облаке
            if op_data.get('done', False):
                if 'error' in op_data:
                    print(f"[ОШИБКА ОБРАБОТКИ]: {op_data['error']}")
                    return None

                # Собираем текстовые блоки воедино
                text_pieces = []
                chunks = op_data.get('response', {}).get('chunks', [])
                for chunk in chunks:
                    for alternative in chunk.get('alternatives', []):
                        if 'text' in alternative:
                            text_pieces.append(alternative['text'])

                return " ".join(text_pieces)

    except Exception as err:
        print(f"[ОШИБКА gRPC]: {err}")
        return None


# ГЛАВНАЯ ФУНКЦИЯ ДЛЯ ВЫЗОВА ИЗ ДРУГИХ СКРИПТОВ
def transcribe_audio_file(input_audio_path, output_text_path):
    """
    Принимает путь к аудио (.wav/.pcm) и путь, куда сохранить текст.
    Возвращает True в случае успеха, False при ошибке.
    """
    env_token = os.environ.get("IAM_TOKEN")
    env_api_key = os.environ.get("SPEECHKIT_API_KEY")
    env_folder_id = os.environ.get("FOLDER_ID")
    bucket_name = os.environ.get("BUCKET_NAME")

    # Проверка обязательных переменных (нужен хотя бы один рабочий токен/ключ)
    if not (env_token or env_api_key) or not env_folder_id or not bucket_name:
        print("[ОШИБКА] IAM_TOKEN/SPEECHKIT_API_KEY, FOLDER_ID или BUCKET_NAME не заданы в .env")
        return False

    if not os.path.exists(input_audio_path):
        print(f"[ОШИБКА] Файл не найден: {input_audio_path}")
        return False

    audio_working_path = input_audio_path
    is_temp_file = False
    temp_pcm_path = "../data/inbox_audio_test/temp_converted_audio.pcm"

    # Обработка конвертации из WAV в PCM
    if input_audio_path.lower().endswith('.wav'):
        if convert_wav_to_pcm(input_audio_path, temp_pcm_path):
            audio_working_path = temp_pcm_path
            is_temp_file = True
        else:
            return False
    elif not input_audio_path.lower().endswith('.pcm'):
        print("[ОШИБКА] Неподдерживаемый формат файла")
        return False

    # Генерация уникального имени объекта в бакете на основе текущего времени
    file_name_raw = os.path.basename(audio_working_path)
    name_part, ext_part = os.path.splitext(file_name_raw)
    object_name = f"{name_part}_{int(time.time())}{ext_part}"

    # 1. Загрузка файла в бакет
    file_uri = upload_to_bucket(audio_working_path, bucket_name, object_name)
    if not file_uri:
        if is_temp_file and os.path.exists(temp_pcm_path):
            os.remove(temp_pcm_path)
        return False

    # 2. Передаем ссылку на бакет в SpeechKit и запускаем асинхронный процесс
    recognized_text = run_async_grpc_stt(env_folder_id, env_token, file_uri, api_key=env_api_key)

    # 3. Полная очистка временных файлов везде
    delete_from_bucket(bucket_name, object_name)

    if is_temp_file and os.path.exists(temp_pcm_path):
        os.remove(temp_pcm_path)

    # 4. Сохранение результата транскрибации в файл
    if recognized_text:
        os.makedirs(os.path.dirname(output_text_path), exist_ok=True)
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(recognized_text)
        print(f"[STT] Успешно сохранено в {output_text_path}")
        return True

    print("[STT] Не удалось распознать аудио или пустой ответ")
    return False


if __name__ == '__main__':
    transcribe_audio_file("../data/inbox_audio/greenhushing.wav", "../data/outbox_audio_test/transcript.txt")