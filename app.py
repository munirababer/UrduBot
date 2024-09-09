import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from gtts import gTTS
import os
import base64
import tempfile
import google.generativeai as genai
import time

# Retrieve API key from Streamlit secrets
GEMINI_API_KEY = "AIzaSyBL_-rinB4ETEWmbYrka8pSEyihtqCQgd0"
genai.configure(api_key=GEMINI_API_KEY)

# Main function
def main():
    
    st.markdown("<h1 class='header-text'> Urdu Voice Chatbot</h1>", unsafe_allow_html=True)
    st.subheader('"اردو وائس باٹ" ', divider='blue')
    st.sidebar.header("اردو چیٹ باٹ", divider='blue')
    st.sidebar.write('''یہ ایک اردو وائس چیٹ بوٹ ہے۔ اس میں اردو وائس ان پٹ لیتا ہے اور اردو ٹیکسٹ کے ساتھ اردو آواز میں جواب دیتا ہے۔ ''')

   
    with st.container():
        st.markdown('<div class="audio-recorder-container">', unsafe_allow_html=True)
    # Audio recorder for Urdu input
    audio_data = audio_recorder(text='آواز ریکارڈ کروائیں', icon_size="2x", icon_name="microphone-lines", key="urdu_recorder")
    st.markdown('</div>', unsafe_allow_html=True)

    if audio_data is not None:
        with st.container():
            col1, col2 = st.columns(2)

            with col2:
                # Display the recorded audio file
                st.audio(audio_data)
                
                # Save the recorded audio to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                    temp_audio_file.write(audio_data)
                    temp_audio_file_path = temp_audio_file.name

                # Convert audio file to text
                text = convert_audio_to_text(temp_audio_file_path)
                st.markdown(f'<div class="user-text">{text}</div>', unsafe_allow_html=True)

                # Remove the temporary file
                os.remove(temp_audio_file_path)

        # Get response from the LLM model
        response_text = get_llm_response(text)

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Convert the response text to speech
                response_audio_html = convert_text_to_audio(response_text)

                st.markdown(f'<div class="bot-text">{response_text}</div>', unsafe_allow_html=True)

def convert_audio_to_text(audio_file_path):
    # Convert Urdu audio to text using speech recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="ur")
            return text
        except sr.UnknownValueError:
            return "آپ کی آواز واضح نہیں ہے"
        except sr.RequestError:
            return "Sorry, my speech service is down"

def convert_text_to_audio(text, lang='ur'):
    try:
        tts = gTTS(text=text, lang=lang)
        tts_audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        tts.save(tts_audio_path)

        # Directly use st.audio with the file path
        st.audio(tts_audio_path, format='audio/mp3')
    except Exception as e:
        st.error(f"Error converting text to audio: {e}")

def encode_audio_to_base64(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    return base64.b64encode(audio_bytes).decode()

def get_llm_response(text, retries=3, delay=5):
    prompt = f"""Kindly answer this question in Urdu language. 
    Don't use any other language or characters from other languages.
    Use some Urdu words at the beginning and end of your answer related to the question. 
    Keep your answer short. 
    You can also ask anything related to the topic in Urdu.
    If you don't know the answer or don't understand the question, 
    Respond with 'I did not get what you speak, please try again' in Urdu.
    Question: {text}"""

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    for attempt in range(retries):
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )

            chat_session = model.start_chat()
            response = chat_session.send_message(prompt)

            return response.text
        except Exception as e:
            st.error(f"Error while fetching response from LLM: {e}")
            time.sleep(delay)  # Wait before retrying
            if attempt == retries - 1:
                return "Sorry, there was an error processing your request."

if __name__ == "__main__":
    main()
