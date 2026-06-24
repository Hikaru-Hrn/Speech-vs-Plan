import speech_recognition as sr

st = sr.Recognizer()

with sr.Microphone() as mic:
    st.adjust_for_ambient_noise(source=mic, duration=0.5)
    audio = st.listen(source=mic)
    query = st.recognize_google(audio_data=audio, language='ru-RU').lower()
print(query)