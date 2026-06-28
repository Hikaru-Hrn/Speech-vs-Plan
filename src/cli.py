import typer

from transcribe import transcribe_audio_file

def main(input: str, output:str):
    """
    Тест Yandex SpeechKit
    """
    return transcribe_audio_file(input, output)


if __name__ == "__main__":
    typer.run(main)