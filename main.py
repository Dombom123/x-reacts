import os
import cv2
import base64
import time
import requests
from openai import OpenAI
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip

from moviepy.audio.fx.all import volumex
from moviepy.video.compositing.concatenate import concatenate_videoclips
import numpy as np

import streamlit as st
from PIL import Image
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

def generate_text_from_frames(prompt, path_to_video, base64Frames):
    api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    # Get the audio from the video
    audio = AudioFileClip(path_to_video)
    audio.write_audiofile("speech.mp3")
    audio_file = open("speech.mp3", "rb")
    transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )

    text_content = transcript.text
    print(text_content)

    st.subheader("Transcript")
    st.write(text_content)
    
    video_length_in_seconds = len(base64Frames) / 30
    st.write(f"Video Length: {video_length_in_seconds} seconds")
    max_frames = 20
    frame_divider = len(base64Frames) // max_frames

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                f"""{prompt}. Das Video ist {video_length_in_seconds} Sekunden lang.
                Das ist das Audiotranskript des Videos: {text_content}. Das sind Frames aus dem Video:""",
                
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::frame_divider]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 100,
    }
    result = client.chat.completions.create(**params)
    return result.choices[0].message.content

def generate_audio_from_text(text):
    api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "tts-1-1106",
            "input": text,
            "voice": "onyx",
        },
    )

    audio = b""
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        audio += chunk

    # Write audio bytes to a file
    with open('audio.mp3', 'wb') as f:
        f.write(audio)
        f.close()
    print("Audio saved to audio.mp3")
    st.write("Audio saved to audio.mp3")
    filepath = 'audio.mp3'

    return filepath

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
        "source_url": "https://i.ibb.co/b6S8DYJ/Bildschirmfoto-2023-11-17-um-10-22-22-removebg-preview.png"
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
    path = "avatar.mp4"
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




def assemble_video(gen_path, original_video_path, audio_path):

    # Load the original video, the avatar video, and the audio
    original_video = VideoFileClip(original_video_path)
    avatar_video = VideoFileClip(gen_path)
    audio = AudioFileClip(audio_path)

    # Lower the volume of the original video
    original_video = original_video.volumex(0.1)  # Adjust the volume level as needed

    # Check if the avatar video is longer than the original video
    if avatar_video.duration > original_video.duration:
        # Calculate how many times the original video needs to be repeated
        repeat_times = int(np.ceil(avatar_video.duration / original_video.duration))
        # Repeat the original video
        original_video = concatenate_videoclips([original_video] * repeat_times)

    # Make the original video loop for the full length of the avatar video
    original_video = original_video.loop(duration=avatar_video.duration)

    # Resize the avatar video to the desired size and position it at the bottom right corner
    avatar_video = avatar_video.resize(height=original_video.h // 4).set_position(('right', 'bottom'))

    # Overlay the avatar video on the original video
    composite_video = CompositeVideoClip([original_video, avatar_video])

    # Set the audio of the composite video to the audio from audio.mp3
    composite_video = composite_video.set_audio(audio)

    # Write the final video to a file
    composite_video.write_videofile('final.mp4')

def main():
    # Initialize Streamlit
    st.set_page_config(page_title="X-Reacts", page_icon="🎥")

    st.title("Reactions from Hell")
    st.markdown(
        """
        This app generates **a reaction video** from a video uploaded by the user.
        """
    )
    st.image("header.png")


    # drop down menu
    st.subheader("Step 1: Choose a prompt")
    prompts = {
        "Default": """Wir spielen ein Rollenspiel. Sag einen Satz zu den Bildern als wärst du Satan, ein fieser und witziger Instagramteufel. """,
        "Custom": """Wir spielen ein Rollenspiel. Sag einen Satz zu den Bildern als wärst du Satan, ein fieser und witziger Instagramteufel. """,
    }
    default_prompt = """Wir spielen ein Rollenspiel. Sag einen Satz zu den Bildern als wärst du Satan, ein fieser und witziger Instagramteufel. """

    prompt = st.selectbox("Choose a prompt", list(prompts.keys()))
    if prompt == "Custom":
        prompt = st.text_area('Enter your prompt', default_prompt)


    
    st.subheader("Step 2: Upload a video")
    uploaded_file = st.file_uploader("Choose a video file", type=['mp4'], key='video', help='Upload a video file to get a reaction video')

    if st.button('Start generating') and uploaded_file is not None:
        with open('temp_video.mp4', 'wb') as f:
            bar = st.progress(5)
            f.write(uploaded_file.read())
        with st.spinner('Processing the video...'):
            path_to_video = 'temp_video.mp4'
            bar.progress(10)
            base64Frames = read_frames_from_video(path_to_video)
            bar.progress(15)
            text = generate_text_from_frames(prompt, path_to_video, base64Frames)
            bar.progress(20)
            st.subheader("Voiceover Text")
            st.write(text)
            audio_path = generate_audio_from_text(text) 
            bar.progress(30)          
            audio_url = upload_audio_to_did(audio_path)
            bar.progress(50)
            gen_video_path = generate_video_from_audio(audio_url)
            bar.progress(80)
            assemble_video(gen_video_path, path_to_video, audio_path)
            bar.progress(100)
            st.success('Done!')
            st.subheader("Generated Video")
            video_file = open('final.mp4', 'rb')

            video_bytes = video_file.read()
            st.markdown(
                f"""
                <video width="320" height="240" controls>
                    <source src="data:video/mp4;base64,{base64.b64encode(video_bytes).decode()}" type="video/mp4">
                </video>
                """,
                unsafe_allow_html=True,
            )

if __name__ == "__main__":
    main()