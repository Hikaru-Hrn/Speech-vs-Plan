import typer
import json
from pathlib import Path

from analyze import get_access_token, ask_with_file_content
from transcribe import transcribe_audio_file

GET_TOKEN_PARAMS_FILE = 'get_access_token.json'
SAVE_TOKEN_FILE = 'access_token.json'

data_path = Path("../data/")

def main(tokens: bool = typer.Option(False, "--tokens", "-t", help="Обновить токены (Yandex, Gigachat)"),
         input_audio_file: str = typer.Option(None, "--input", "-i", help="Путь у входному аудиофайлу (формат wav)"),
         output_audio2text: str = typer.Option(None, "--output-text", "-o", help="Директория для сохранения текста из аудио (по умолчанию data/outbox_audio2text)"),
         input_plan: str = typer.Option(None, "--input-plan", "-p", help="Путь к "),
         result:str = typer.Option(None, "--result", "-r", help="Путь к результату (по умолчанию result/result.txt)"),
         ):
    """
    CLI-утилита для транскрибации аудио и последующего анализа текста нейросетью.
    """
    if tokens:
        # Yandex SpeechKit
        typer.secho("=== Настройка Yandex SpeechKit ===", fg=typer.colors.BLUE)
        iam_token = input("Введите IAM токен: ")
        folder_id = input("Введите FOLDER_ID: ")

        with open("../.testenv", "w", encoding="utf-8") as f:
            f.write(f"IAM_TOKEN={iam_token}\n")
            f.write(f"FOLDER_ID={folder_id}")

        # Gigachat
        cert_path = input("Введите CERT_PATH для gigachat: ")
        auth_data = input("Введите auth_data: ")

        gigachat_config = {
            "url": "https://ngw.devices.sberbank.ru:9443/api/v1/oauth",
            "payload": {"scope": "GIGACHAT_API_PERS"},
            "cert_path": cert_path,
            "auth_data": auth_data
        }
        with open("get_access_token.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(gigachat_config))

        get_access_token()
        typer.secho("Токены успешно сохранены!", fg=typer.colors.BLUE)

        if not input_plan:
            return

    if not input_audio_file or not input_plan:
        typer.secho("Ошибка: Для запуска обработки необходимо указать --input-audio (-i) и --input-plan (-p)", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # аудио
    audio_path = Path(input_audio_file)

    # текст из аудио
    if output_audio2text == None:
        output_audio2text = str(data_path/"{data_path}outbox_audio2text")
        output_audio2text = Path(output_audio2text)
    # output_audio2text.mkdir(parents=True, exist_ok=True)

    plan_path = Path(input_plan)

    # результат
    if result == None:
        result = str(data_path / "result/result.txt")


    actual_output_text_path = output_audio2text / f"{audio_path.stem}.txt"

    transcribe_audio_file(str(audio_path), str(actual_output_text_path))

    with open(result, "w", encoding="utf-8") as f:
        f.write(ask_with_file_content(str(plan_path), str(output_audio2text)))

    typer.secho(f"Готово! Результат сохранен в: {result}", fg=typer.colors.BLUE)


if __name__ == "__main__":
    typer.run(main)