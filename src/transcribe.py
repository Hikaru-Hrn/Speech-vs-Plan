# coding=utf8
import os

import wave
import audioop
import grpc

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
                # В большинстве случаев WAV уже 16-битный, но для страховки:
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


def gen(folder_id, audio_file_name):
    specification = stt_service_pb2.RecognitionSpec(
        language_code='ru-RU',
        profanity_filter=True,
        model='general',
        partial_results=False,
        audio_encoding='LINEAR16_PCM',
        sample_rate_hertz=TARGET_SAMPLE_RATE
    )
    streaming_config = stt_service_pb2.RecognitionConfig(specification=specification, folder_id=folder_id)
    yield stt_service_pb2.StreamingRecognitionRequest(config=streaming_config)

    with open(audio_file_name, 'rb') as f:
        data = f.read(CHUNK_SIZE)
        while data != b'':
            yield stt_service_pb2.StreamingRecognitionRequest(audio_content=data)
            data = f.read(CHUNK_SIZE)


def run_grpc_stt(folder_id, iam_token, audio_file_name):
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stub = stt_service_pb2_grpc.SttServiceStub(channel)

    try:
        it = stub.StreamingRecognize(gen(folder_id, audio_file_name), metadata=(
            ('authorization', 'Bearer %s' % iam_token),
        ))

        text_pieces = []
        for r in it:
            try:
                if r.chunks[0].final:
                    for alternative in r.chunks[0].alternatives:
                        text_pieces.append(alternative.text)
            except LookupError:
                pass

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
    env_folder_id = os.environ.get("FOLDER_ID")

    if not env_token or not env_folder_id:
        print("[ОШИБКА] IAM_TOKEN или FOLDER_ID не заданы в .env")
        return False

    if not os.path.exists(input_audio_path):
        print(f"[ОШИБКА] Файл не найден: {input_audio_path}")
        return False

    audio_working_path = input_audio_path
    is_temp_file = False
    temp_pcm_path = "../data/inbox_audio_test/temp_converted_audio.pcm"

    # Обработка конвертации
    if input_audio_path.lower().endswith('.wav'):
        if convert_wav_to_pcm(input_audio_path, temp_pcm_path):
            audio_working_path = temp_pcm_path
            is_temp_file = True
        else:
            return False
    elif not input_audio_path.lower().endswith('.pcm'):
        print("[ОШИБКА] Неподдерживаемый формат файла")
        return False

    print(f"[STT] Отправка {audio_working_path} в Yandex Cloud...")
    recognized_text = run_grpc_stt(env_folder_id, env_token, audio_working_path)

    # Чистим временный PCM файл, если он создавался
    if is_temp_file and os.path.exists(temp_pcm_path):
        os.remove(temp_pcm_path)

    if recognized_text:
        # Создаем папку для ответа, если её нет
        os.makedirs(os.path.dirname(output_text_path), exist_ok=True)
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(recognized_text)
        print(f"[STT] Успешно сохранено в {output_text_path}")
        return True

    return False