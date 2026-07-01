import typer
import json
import requests
import os
import time
import uuid
from pathlib import Path

from analyze import get_access_token, ask_with_file_content, _form_request
from transcribe import transcribe_audio_file

GET_TOKEN_PARAMS_FILE = 'get_access_token.json'
SAVE_TOKEN_FILE = 'access_token.json'

data_path = Path("../data/")


def get_unique_path(target_dir: Path, filename_stem: str, extension: str) -> Path:
    """
    Создает уникальный путь к файлу. Если файл уже существует,
    добавляет числовой индекс: text.txt -> text1.txt -> text2.txt
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate = target_dir / f"{filename_stem}{extension}"
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = target_dir / f"{filename_stem}{counter}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1


def fetch_and_save_gigachat_token_safely() -> bool:
    """
    Самостоятельно и безопасно запрашивает токен у GigaChat.
    Формирует структуру в соответствии с требованиями API v2.
    Возвращает True в случае успеха.
    """
    if not os.path.exists(GET_TOKEN_PARAMS_FILE):
        return False

    try:
        with open(GET_TOKEN_PARAMS_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        url = config.get("url", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")

        # АВТО-ИСПРАВЛЕНИЕ: Принудительно переводим с v1 на v2, чтобы SynGX не выдавал 400 Bad Request
        if "/v1/" in url:
            url = url.replace("/v1/", "/v2/")

        auth_data = config.get("auth_data", "")
        # СТРОГАЯ ОЧИСТКА: Удаляем пробелы и переносы строк, которые гарантированно ломают заголовки
        auth_data = auth_data.strip().replace("\n", "").replace("\r", "")

        cert_path = config.get("cert_path", "russian_trusted_root_ca_pem.crt")
        scope = config.get("payload", {}).get("scope", "GIGACHAT_API_PERS")

        if not auth_data:
            typer.secho("Ошибка: В конфигурации отсутствует auth_data!", fg=typer.colors.RED)
            return False

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_data}"
        }
        payload = {"scope": scope}

        verify_val = cert_path if os.path.exists(cert_path) else False
        if not verify_val:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        res = requests.post(url, headers=headers, data=payload, verify=verify_val, timeout=15)

        if res.status_code == 200:
            res_data = res.json()
            token_info = {
                "access_token": res_data["access_token"],
                "expires_at": res_data["expires_at"]
            }
            with open(SAVE_TOKEN_FILE, 'w', encoding='utf-8') as tf:
                json.dump(token_info, tf, indent=4)
            return True
        else:
            typer.secho(f"[Ошибка Сбера] Код: {res.status_code}, URL: {url}", fg=typer.colors.RED)
            typer.secho(f"Ответ сервера:\n{res.text}", fg=typer.colors.YELLOW)
            return False

    except Exception as e:
        typer.secho(f"[Исключение при получении токена]: {e}", fg=typer.colors.RED)
        return False


def check_or_refresh_token():
    """
    Проверяет существование и валидность токена.
    Если он просрочен или отсутствует — генерирует новый.
    """
    token_file = Path(SAVE_TOKEN_FILE)
    need_refresh = True

    if token_file.exists():
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data and isinstance(data, dict) and data.get('expires_at', 0) > int(time.time() * 1000):
                need_refresh = False
        except Exception:
            pass

    if need_refresh:
        typer.echo("Токен GigaChat отсутствует или просрочен. Обновляем...")
        success = fetch_and_save_gigachat_token_safely()
        if not success:
            typer.secho("Ошибка: Не удалось обновить токен GigaChat. Дальнейший анализ невозможен.",
                        fg=typer.colors.RED)
            raise typer.Exit(code=1)


def main(
        tokens: bool = typer.Option(False, "--tokens", "-t", help="Обновить токены (.env и GigaChat)"),
        input_audio_file: str = typer.Option(None, "--input", "-i", help="Путь к входному аудиофайлу (data/inbox_audio)"),
        output_audio2text: str = typer.Option(None, "--output-text", "-o", help="Директория или файл для текста (data/outbox_audio2text)"),
        input_plan: str = typer.Option(None, "--input-plan", "-p", help="Путь к файлу с планом (data/inbox_plan)"),
        result: str = typer.Option(None, "--result", "-r", help="Директория для сохранения результатов (data/result)"),
        mode: str = typer.Option("full", "--mode", "-m", help="Режим: full, transcribe (только Yandex), analyze (только GigaChat)"),
):
    """
    CLI-утилита для транскрибации аудио через Yandex SpeechKit API и анализа текста в GigaChat.
    """
    # === 1. БЛОК ОБНОВЛЕНИЯ КОНФИГУРАЦИИ И ТОКЕНОВ ===
    if tokens:
        typer.secho("=== Настройка Yandex SpeechKit API & Object Storage ===", fg=typer.colors.BLUE)
        folder_id = typer.prompt("Введите FOLDER_ID")
        bucket_name = typer.prompt("Введите BUCKET_NAME")
        aws_access_key_id = typer.prompt("Введите AWS_ACCESS_KEY_ID")
        aws_secret_access_key = typer.prompt("Введите AWS_SECRET_ACCESS_KEY")
        speechkit_api_key = typer.prompt("Введите SPEECHKIT_API_KEY")

        with open("../.env", "w", encoding="utf-8") as f:
            f.write(f"FOLDER_ID={folder_id}\n")
            f.write(f"BUCKET_NAME={bucket_name}\n")
            f.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
            f.write(f"SPEECHKIT_API_KEY={speechkit_api_key}\n")

        typer.secho("=== Настройка GigaChat ===", fg=typer.colors.BLUE)
        auth_data = typer.prompt("Введите auth_data")

        gigachat_config = {
            "url": "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",  # Изначально пишем v2
            "payload": {"scope": "GIGACHAT_API_PERS"},
            "cert_path": "russian_trusted_root_ca_pem.crt",
            "auth_data": auth_data.strip()
        }

        with open(GET_TOKEN_PARAMS_FILE, "w", encoding="utf-8") as f:
            json.dump(gigachat_config, f, indent=4)

        typer.echo("Запрос стартового токена GigaChat...")
        if not fetch_and_save_gigachat_token_safely():
            raise typer.Exit(code=1)

        typer.secho("Все конфигурации успешно обновлены и проверены!", fg=typer.colors.GREEN)

        if mode == "full" and not input_audio_file and not input_plan:
            return

    # Определение логики работы пайплайна
    run_transcribe = mode in ("full", "transcribe")
    run_analyze = mode in ("full", "analyze")

    actual_output_text_path = None

    # === 2. ЭТАП ТРАНСКРИБАЦИИ ===
    if run_transcribe:
        if not input_audio_file:
            typer.secho("Ошибка: Укажите аудиофайл через --input (-i)", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        audio_path = Path(input_audio_file)
        out_text_dir = Path(output_audio2text) if output_audio2text else (data_path / "outbox_audio2text")

        actual_output_text_path = get_unique_path(out_text_dir, audio_path.stem, ".txt")

        typer.echo(f"Транскрибация {audio_path.name} -> {actual_output_text_path.name}...")
        transcribe_audio_file(str(audio_path), str(actual_output_text_path))
    else:
        if not output_audio2text:
            typer.secho("Ошибка: Для анализа укажите путь к готовому тексту через --output-text (-o)",
                        fg=typer.colors.RED)
            raise typer.Exit(code=1)
        actual_output_text_path = Path(output_audio2text)

    # === 3. ЭТАП АНАЛИЗА GIGACHAT ===
    if run_analyze:
        if not input_plan:
            typer.secho("Ошибка: Укажите файл плана через --input-plan (-p)", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        if not actual_output_text_path.exists():
            typer.secho(f"Ошибка: Файл с текстом не найден: {actual_output_text_path}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        plan_path = Path(input_plan)
        result_dir = Path(result) if result else (data_path / "result")

        actual_result_path = get_unique_path(result_dir, "result", ".txt")

        # Проверяем и обновляем токен через безопасную функцию v2 перед запуском analyze.py
        check_or_refresh_token()

        typer.echo("Анализ текста через GigaChat API...")
        response = ask_with_file_content(str(plan_path), str(actual_output_text_path))

        if isinstance(response, requests.Response):
            if response.status_code == 200:
                try:
                    analysis_result = response.json()["choices"][0]["message"]["content"]
                except (KeyError, ValueError):
                    analysis_result = response.text
            else:
                typer.secho(f"Ошибка API GigaChat ({response.status_code}): {response.text}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
        else:
            analysis_result = str(response)

        with open(actual_result_path, "w", encoding="utf-8") as f:
            f.write(analysis_result)

        typer.secho(f"Готово! Результат сохранен в: {actual_result_path}", fg=typer.colors.BLUE)


if __name__ == "__main__":
    typer.run(main)