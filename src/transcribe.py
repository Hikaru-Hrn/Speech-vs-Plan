# coding=utf8
import os
import sys
import grpc
from cloudapi.output.transcribe import transcribe_audio_file


# Тест вызова функции транскрибации с помощью Yandex SpeechKit
if __name__ == '__main__':
    transcribe_audio_file("../data/inbox_audio_test/Запись.wav", "../data/outbox_audio_test/transcript.txt")