import os
import cv2
import base64
import time
import requests
import numpy as np
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import AudioFileClip

import shutil
import subprocess

from openai import OpenAI
from elevenlabs import generate, Voice, VoiceSettings,set_api_key
import streamlit as st

from utils.edit_video import assemble_video

def download_video(url, output_path='data/input.mp4'):
    if url:
        try:
            command = ['yt-dlp', '--force-overwrites', '-o', output_path, url]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                st.success('Download completed successfully.')
                st.text(result.stdout.decode())  # Added for debugging
            else:
                st.error(f'Error: {result.stderr.decode()}')
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')
    else:
        st.error('Please enter a valid URL.')
    return output_path

def read_frames_from_video(path_to_video):
    # Check if the video file exists
    if not os.path.exists(path_to_video):
        raise FileNotFoundError(f"The video file {path_to_video} does not exist.")

    video = cv2.VideoCapture(path_to_video)
    base64Frames = []
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()
    return base64Frames

def generate_transcript(path_to_video):
    api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    # Get the audio from the video
    audio = AudioFileClip(path_to_video)
    audio.write_audiofile("data/speech.mp3")
    audio_file = open("data/speech.mp3", "rb")
    transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )

    text_content = transcript.text
    print(text_content)

    st.subheader("Transcript")
    st.write(text_content)

    return text_content

def generate_text_from_video(path_to_video):
    api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    base64Frames = read_frames_from_video(path_to_video)
    transcript = generate_transcript(path_to_video)
    video_length_in_seconds = len(base64Frames) / 30
    st.write(f"Video Length: {video_length_in_seconds} seconds")
    max_frames = 10
    frame_divider = len(base64Frames) // max_frames
    st.write(f"Number of frames: {len(base64Frames)}")
    st.write(f"Number of frames to use: {max_frames}")
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                f"""Bitte generiere eine detaillierte Zusammenfassung von Informationen über ein Tik Tok Video. Du kannst auch Details hinzufügen bei denen du dir unsicher bist, aber bleibe Konkret und stelle Vermutungen als Aussage dar. Das Video ist {video_length_in_seconds} Sekunden lang.
                Das ist das Audiotranskript des Videos: {transcript}. Das sind Frames aus dem Video:""",
                
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::frame_divider]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 500,
    }
    result = client.chat.completions.create(**params)
    st.subheader("GPT Vision Text")
    st.write(result.choices[0].message.content)
    return result.choices[0].message.content

def generate_voiceover_from_text(prompt, text):
    api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)

    PROMPT_MESSAGES = [
        {
            "role": "system",
            "content": f"{prompt}"
        },
        {
            "role": "user",
            "content": f"Generiere einen kurzen Kommentar zu dem Video. Antwortschema: <Kommentar in 3-4 Sätzen>. Kein Prefix oder Überschrift. Hier ist die Zusammenfassung des Videos: {text}. Jetzt kommt dein Kommentar:"
        },
    ]
    params = {
        "model": "gpt-4",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 150,
    }
    result = client.chat.completions.create(**params)
    st.subheader("Voiceover Text")
    st.write(result.choices[0].message.content)
    return result.choices[0].message.content


def generate_audio_from_text(text):
    set_api_key(st.secrets["11"]["11LABS_API_KEY"])
    audio = generate(
        model='eleven_multilingual_v2',
        text=text,
        voice=Voice(
            voice_id='qB21fQlUsqrLQbytfdqA',
            settings=VoiceSettings(stability=0.5, similarity_boost=0.8, style=0.5, use_speaker_boost=True)
        )
    )
    # Write audio bytes to a file
    with open('data/audio.mp3', 'wb') as f:
        f.write(audio)
        f.close()

    
    print("Audio saved to audio.mp3")
    # st.write("Audio saved to audio.mp3")
    filepath = 'data/audio.mp3'
    return filepath 

def prepend_silence(audio_path, silence_duration):
    audio_clip = AudioSegment.from_file(audio_path)
    silent_segment = AudioSegment.silent(duration=silence_duration * 1000)
    new_audio = silent_segment + audio_clip
    new_audio.export(audio_path, format='mp3')

def append_silence(audio_path, silence_duration):
    audio_clip = AudioSegment.from_file(audio_path)
    silent_segment = AudioSegment.silent(duration=silence_duration * 1000)
    new_audio = audio_clip + silent_segment
    new_audio.export(audio_path, format='mp3')



def generate_video_from_audio(audio_url):


    url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "audio",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            },
            "ssml": "false",
            "audio_url": audio_url
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0",
            "stitch": True
        },
        "source_url": "https://i.imgur.com/4b1cCxf.jpeg"
    }
    authorization = st.secrets["d-id"]["authorization"]
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": authorization
    }

    response = requests.post(url, json=payload, headers=headers)

    video_id = response.json()["id"]
    url = f"https://api.d-id.com/talks/{video_id}"

    # Retry the request until the 'result_url' is available
    while True:
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if "result_url" in response_json:
            print(response_json["result_url"])
            url = response_json["result_url"]
            break

        print("Waiting for result_url...")
        st.write("Waiting for result_url...")
        time.sleep(5)  # wait for 5 seconds before retrying

    # Download from url
    path = "data/avatar.mp4"
    response = requests.get(url)
    with open(path, "wb") as f:
        f.write(response.content)
        

    return path

def upload_audio_to_did(audio_path):

    url = "https://api.d-id.com/audios"
    authorization = st.secrets["d-id"]["authorization"]

    files = { "audio": (audio_path, open(audio_path, "rb"), "audio/mpeg") }
    headers = {
        "accept": "application/json",
        "authorization": authorization
    }

    response = requests.post(url, files=files, headers=headers)
    return response.json()["url"]



def generate_text_for_video(uploaded_file, prompt, progress_bar):
    # Define the path for the temporary video file
    path_to_video = 'data/temp_video.mp4'
    
    # Check if uploaded_file is a file-like object
    if hasattr(uploaded_file, 'read'):
        # File-like object from Streamlit's uploader
        with open(path_to_video, 'wb') as f:
            f.write(uploaded_file.read())
    elif isinstance(uploaded_file, str):
        # String (file path from YouTube download)
        # Assuming the file already exists at the path, so just update the path
        path_to_video = uploaded_file
    else:
        raise ValueError("Invalid input type for uploaded_file")

    progress_bar.progress(10)

    # Rest of your processing logic...
    vision_text = generate_text_from_video(path_to_video)
    voiceover_text = generate_voiceover_from_text(prompt, vision_text)

    progress_bar.progress(20)

    return voiceover_text, path_to_video


def process_video_with_text(text, path_to_video, progress_bar):
    audio_path = generate_audio_from_text(text)
    progress_bar.progress(30)
    # Wait for 5 seconds
    # time.sleep(5)
    prepend_silence(audio_path, 6)
    append_silence(audio_path, 0.5)

    audio_url = upload_audio_to_did(audio_path)
    progress_bar.progress(50)

    gen_video_path = generate_video_from_audio(audio_url)
    progress_bar.progress(80)

    assemble_video(gen_video_path, path_to_video, audio_path)
    progress_bar.progress(100)

    return open('data/final.mp4', 'rb')

def display_video(video_file):
    st.video(video_file)

def main():
    st.set_page_config(page_title="X-Reacts", page_icon="🎥")
    st.title("X-Reacts Video Generation 🎥")
    st.image("data/header.png")

    st.subheader("Step 1: Select a prompt")
    prompts = {
"Default": 
"""Du schreibst witzige Kommentare zu Tik Tok Videos in weniger als 5 Sätzen.Du bist der Teufel.
Du bist sarkastisch und hast starke, kontroverse Meinungen.
Nachdem du Jahrzehntelang in der Hölle warst, bist du nun an die Erdoberfläche gelangt.
Du versuchst, die moderne Gesellschaft zu verstehen, es fällt dir aber schwer.
Du liebst es zu sündigen und andere zum sündigen zu verleiten.""",
"Custom": 
"""Du schreibst witzige Kommentare zu Tik Tok Videos in weniger als 5 Sätzen.
Du bist der Teufel.
Du bist sarkastisch und hast starke, kontroverse Meinungen.
Nachdem du Jahrzehntelang in der Hölle warst, bist du nun an die Erdoberfläche gelangt.
Du versuchst, die moderne Gesellschaft zu verstehen, es fällt dir aber schwer.
Du liebst es zu sündigen und andere zum sündigen zu verleiten."""
    }
    prompt_selection = st.selectbox("Prompt Selection:", list(prompts.keys()))
    if prompt_selection == "Custom":
        prompt = st.text_area('Enter your prompt', prompts[prompt_selection])
    else:
        prompt = prompts[prompt_selection]

    st.subheader("Step 2: Upload a video")
    uploaded_file = st.file_uploader("Choose a video file:", type=['mp4'], key='video')
    url = st.text_input('Enter the video URL here:')
    
    # Toggle for activating video generation
    is_generation_activated = st.toggle('Activate Video Generation')

    if st.button('Download Video from URL'):
        with st.spinner('Downloading video...'):
            bar = st.progress(5)
            path_to_video = download_video(url)
        with st.spinner('Generating text...'):
            text, path_to_video = generate_text_for_video(path_to_video, prompt, bar)
            st.success('Text generated!')
        with st.spinner('Processing the video...'):
            video_file = process_video_with_text(text, path_to_video, bar)
            st.success('Done!')
            st.subheader("Generated Video")
            display_video(video_file)


        
    # Button to start generating
    if st.button('Start generating'):
        # Check if the toggle is activated and a file is uploaded
        if is_generation_activated and uploaded_file is not None:
            bar = st.progress(5)
            with st.spinner('Generating text...'):
                text, path_to_video = generate_text_for_video(uploaded_file, prompt, bar)
                st.success('Text generated!')

            with st.spinner('Processing the video...'):
                video_file = process_video_with_text(text, path_to_video, bar)
                st.success('Done!')
                st.subheader("Generated Video")
                display_video(video_file)
        elif not is_generation_activated and uploaded_file is not None:
            bar = st.progress(5)
            with st.spinner('Dev mode: Generating only text...'):
                text, path_to_video = generate_text_for_video(uploaded_file, prompt, bar)
                st.success('Text generated!')
        else:
            st.warning("Please upload a video to proceed.")


if __name__ == "__main__":
    main()
