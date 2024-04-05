import streamlit as st
import speech_recognition as sr
from io import BytesIO
from docx import Document
from moviepy.editor import *
import os
import tempfile
import base64
from database import create_connection, create_search_history_table, add_to_history, get_search_history

# Function to convert speech to text
def speech_to_text(audio_data, timeout=60):
    recognizer = sr.Recognizer()
    with audio_data as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            st.error("Speech recognition timed out. Please try again.")
            return ""
    return text

# Function to convert video to audio
def extract_audio(video_file):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(video_file.read())
        temp_file_path = temp_file.name

    video = VideoFileClip(temp_file_path)
    audio_file_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_file_path)
    
    # Close the audio file to ensure it's fully written and closed
    video.close()

    # Delete the temporary video file
    os.unlink(temp_file_path)

    return audio_file_path

# Function to generate Word document
def generate_word_document(text):
    doc = Document()
    doc.add_paragraph(text)
    return doc

# Function for live transcription
def live_transcription(conn):
    st.subheader("Live Transcription")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Speak something...")
        audio_data = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio_data)
        st.success("Live Transcription Result: " + text)
        add_to_history(conn, "Live", text)  # Add transcribed text to search history with search type "Live"
    except sr.UnknownValueError:
        st.error("Could not understand audio")
    except sr.RequestError as e:
        st.error("Could not request results; {0}".format(e))

# Function to handle audio file upload and conversion
def audio_file_to_text(audio_file, conn):
    st.audio(audio_file, format="audio/wav")
    audio_file_path = audio_file
    if st.button("Transcribe"):
        audio_data = sr.AudioFile(audio_file_path)
        text = speech_to_text(audio_data)
        st.text_area("Transcribed Text", value=text, height=200)
        add_to_history(conn, "Audio", text)  # Add transcribed text to search history with search type "Audio"
        # Download button for the transcribed text
        st.markdown(get_download_link(text, "transcribed_text.txt"), unsafe_allow_html=True)

# Function to handle video file upload and conversion
def video_file_to_text(video_file, conn):
    st.video(video_file)
    audio_file_path = extract_audio(video_file)
    if st.button("Transcribe"):
        audio_data = sr.AudioFile(audio_file_path)
        text = speech_to_text(audio_data)
        st.text_area("Transcribed Text", value=text, height=200)
        add_to_history(conn, "Video", text)  # Add transcribed text to search history with search type "Video"
        # Download button for the transcribed text
        st.markdown(get_download_link(text, "transcribed_text.txt"), unsafe_allow_html=True)

# Function to generate a download link
def get_download_link(text, filename):
    txt = f'{text}'
    b64 = base64.b64encode(txt.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Transcribed Text</a>'
    return href

# Function to display search history
def show_search_history(conn):
    st.subheader("Search History")
    history = get_search_history(conn)
    if history:
        st.write("| SR Number | Search Type | Transcribed Text | Download |")
        st.write("| --- | --- | --- | --- |")
        for idx, item in enumerate(history, start=1):
            parts = item.split(":", 1)
            if len(parts) == 2:
                search_type, transcribed_text = parts
                st.write(f"| {idx} | {search_type.capitalize()} | {transcribed_text.strip()} | [Download](#) |")
            else:
                st.warning(f"Invalid format for item: {item}")
    else:
        st.info("Search history is empty.")

# Create a connection to the database
conn = create_connection('search_history.db')
if conn is not None:
    # Create search history table if it doesn't exist
    create_search_history_table(conn)
else:
    st.error("Error! Cannot create database connection.")

def main():
    st.title("Speech to Text Converter")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    nav_option = st.sidebar.radio("Go to", ("Home", "Live Transcription", "Audio File to Text", "Video File to Text", "Search History"))

    if nav_option == "Home":
        st.write("Welcome to the Speech to Text Converter!")
    elif nav_option == "Live Transcription":
        live_transcription(conn)
    elif nav_option == "Audio File to Text":
        st.write("Upload an audio file:")
        audio_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])
        if audio_file:
            audio_file_to_text(audio_file, conn)
    elif nav_option == "Video File to Text":
        st.write("Upload a video file:")
        video_file = st.file_uploader("Choose a video file", type=["mp4"])
        if video_file:
            video_file_to_text(video_file, conn)
    elif nav_option == "Search History":
        show_search_history(conn)

if __name__ == "__main__":
    main()
