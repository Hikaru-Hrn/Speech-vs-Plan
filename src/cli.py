import typer
from itsdangerous import encoding

from transcribe import transcribe_audio_file

def main(tokens: bool = typer.Option(False, "--tokens", "-t", help="token mod"),
         test: bool = typer.Option(False, "--fefe", "-f", help="test mode")):
    """
    Тест Yandex SpeechKit
    """
    if tokens:
        iam_token = input("Введите IAM токен: ")
        folder_id = input("Введите FOLDER_ID: ")
        with open("../.testenv", "w", encoding="utf-8") as f:
            f.write(f"IAM_TOKEN={iam_token}")
            f.write("\n")
            f.write(f"FOLDER_ID={folder_id}")

if __name__ == "__main__":
    typer.run(main)