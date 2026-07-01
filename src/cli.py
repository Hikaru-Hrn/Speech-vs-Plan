import typer
import json
import requests
import os
import time
from pathlib import Path

# Импортируем инструменты из оригинальных файлов (analyze.py не изменяется)
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


def fix_corrupted_token_file():
    """
    Защита от падения analyze.py.
    Если access_token.json поврежден или содержит null, удаляем его.
    """
    token_file = Path(SAVE_TOKEN_FILE)
    if token_file.exists():
        try:
            if token_file.stat().st_size == 0:
                return
            with open(token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data is None or not isinstance(data, dict) or 'expires_at' not in data:
                token_file.unlink()
        except Exception:
            token_file.unlink()


def main(
        tokens: bool = typer.Option(False, "--tokens", "-t", help="Обновить токены (.env и GigaChat)"),
        input_audio_file: str = typer.Option(None, "--input", "-i",
                                             help="Путь к входному аудиофайлу (data/inbox_audio)"),
        output_audio2text: str = typer.Option(None, "--output-text", "-o",
                                              help="Директория или файл для текста (data/outbox_audio2text)"),
        input_plan: str = typer.Option(None, "--input-plan", "-p", help="Путь к файлу с планом (data/inbox_plan)"),
        result: str = typer.Option(None, "--result", "-r", help="Директория для сохранения результатов (data/result)"),
        mode: str = typer.Option("full", "--mode", "-m",
                                 help="Режим: full, transcribe (только Yandex), analyze (только GigaChat)"),
):
    """
    CLI-утилита для транскрибации аудио через Yandex SpeechKit API и анализа текста в GigaChat.
    """
    # Автоматическое лечение json-файла Сбера при любых сбоях
    fix_corrupted_token_file()

    # === 1. БЛОК ОБНОВЛЕНИЯ КОНФИГУРАЦИИ И ТОКЕНОВ ===
    if tokens:
        typer.secho("=== Настройка Yandex SpeechKit API & Object Storage ===", fg=typer.colors.BLUE)
        folder_id = typer.prompt("Введите FOLDER_ID")
        bucket_name = typer.prompt("Введите BUCKET_NAME")
        aws_access_key_id = typer.prompt("Введите AWS_ACCESS_KEY_ID")
        aws_secret_access_key = typer.prompt("Введите AWS_SECRET_ACCESS_KEY")
        speechkit_api_key = typer.prompt("Введите SPEECHKIT_API_KEY")

        # Сохранение строго 5 актуальных параметров в .env
        with open("../.env", "w", encoding="utf-8") as f:
            f.write(f"FOLDER_ID={folder_id}\n")
            f.write(f"BUCKET_NAME={bucket_name}\n")
            f.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
            f.write(f"SPEECHKIT_API_KEY={speechkit_api_key}\n")

        typer.secho("=== Настройка GigaChat ===", fg=typer.colors.BLUE)
        auth_data = typer.prompt("Введите auth_data")

        gigachat_config = {
            "url": "https://ngw.devices.sberbank.ru:9443/api/v1/oauth",
            "payload": {"scope": "GIGACHAT_API_PERS"},
            "cert_path": "russian_trusted_root_ca_pem.crt",
            "auth_data": auth_data
        }

        with open(GET_TOKEN_PARAMS_FILE, "w", encoding="utf-8") as f:
            json.dump(gigachat_config, f, indent=4)

        typer.echo("Запрос стартового токена GigaChat...")
        token_res = _form_request()

        if token_res is None:
            typer.secho("❌ Ошибка: Не удалось авторизоваться в GigaChat!", fg=typer.colors.RED)
            typer.secho("Проверьте auth_data и наличие файла сертификата 'russian_trusted_root_ca_pem.crt'.",
                        fg=typer.colors.YELLOW)
            if Path(SAVE_TOKEN_FILE).exists():
                Path(SAVE_TOKEN_FILE).unlink()
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

        # Получаем уникальное имя вида lection.txt, lection1.txt и т.д.
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

        # Имя для результата по маске result.txt, result1.txt
        actual_result_path = get_unique_path(result_dir, "result", ".txt")

        typer.echo("Анализ текста через GigaChat API...")

        fix_corrupted_token_file()
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