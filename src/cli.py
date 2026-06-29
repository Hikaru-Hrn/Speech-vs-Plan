import typer
import json
from analyze import _form_request, get_access_token
from transcribe import transcribe_audio_file

GET_TOKEN_PARAMS_FILE = 'get_access_token.json'
SAVE_TOKEN_FILE = 'access_token.json'

def main(tokens: bool = typer.Option(False, "--tokens", "-t", help="add tokens"),
         program: bool = typer.Option(True, "--yandexspeechkit", "-y", help="add yandexspeechkit"),
         input_audio_file: str = typer.Option(None, "--input", "-i", help="input audio file"),
         input_text_plan: str = typer.Option(None, "--input-textplan", "-i", help="input text plan"),
         output_text_file:str = typer.Option(None, "--output-text", "-o", help="output text file")
         ):
    """
    Thank you
    """
    # Yandex SpeechKit
    if tokens:
        iam_token = input("Введите IAM токен: ")
        folder_id = input("Введите FOLDER_ID: ")
        cert_path = input("Введите CERT_PATH для gigachat: ")
        auth_data = input("Введите auth_data: ")

        with open("../.testenv", "w", encoding="utf-8") as f:
            f.write(f"IAM_TOKEN={iam_token}")
            f.write("\n")
            f.write(f"FOLDER_ID={folder_id}")

        gigachat_config = {
            "url": "https://ngw.devices.sberbank.ru:9443/api/v1/oauth",
            "payload": {"scope": "GIGACHAT_API_PERS"},
            "cert_path": cert_path,
            "auth_data": auth_data
        }
        with open("get_access_token.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(gigachat_config))

        get_access_token()

    if program:
        transcribe_audio_file()



if __name__ == "__main__":
    typer.run(main)