import os
import cv2
import base64
import time
import requests
from openai import OpenAI
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.compositing.concatenate import concatenate_videoclips
import numpy as np
from drive_manager import FirebaseManager
import streamlit as st

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

def generate_text_from_frames(path_to_video, base64Frames):

    client = OpenAI()
    # Get the audio from the video
    audio = AudioFileClip(path_to_video)
    audio.write_audiofile("speech.mp3")
    audio_file = open("speech.mp3", "rb")
    transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )
    meta_data = f"{transcript}"
    # Now meta_data contains all key-value pairs
    print(meta_data)
    st.write(meta_data)
    
    video_length_in_seconds = len(base64Frames) / 30
    st.write(video_length_in_seconds)
    max_frames = 20
    frame_divider = len(base64Frames) // max_frames

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                f"""Wir spielen ein Rollenspiel Sag einen Satz zu den Bildern als wärst du Satan, 
                ein fieser und witziger Instagramteufel... {video_length_in_seconds} sekunden... 
                Das ist das Audiotranskript des Videos: {meta_data}""",
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
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
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



def assemble_video(gen_path, original_video_path):

    # Load the original video and the avatar video
    original_video = VideoFileClip(original_video_path)
    avatar_video = VideoFileClip(gen_path)

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

    # Extract the audio from the original video and the avatar video
    original_audio = original_video.audio.volumex(0.01)  # reduce the volume to 1%
    avatar_audio = avatar_video.audio

    # Overlay the audio clips
    overlaid_audio = CompositeAudioClip([original_audio, avatar_audio])

    # Set the audio of the composite video to the overlaid audio
    composite_video = composite_video.set_audio(overlaid_audio)

    # Write the final video to a file
    composite_video.write_videofile('final.mp4')

def main():

        # Use file_uploader to allow the user to upload a video
    st.markdown("# Upload Video")
    uploaded_file = st.file_uploader("Please upload the video file", type=['mp4', 'mov'])

    if uploaded_file is not None:
        with open('temp_video.mp4', 'wb') as f:
            f.write(uploaded_file.read())
        with st.spinner('Processing the video...'):
            path_to_video = 'temp_video.mp4'
            base64Frames = read_frames_from_video(path_to_video)
            text = generate_text_from_frames(path_to_video, base64Frames)
            st.markdown("## Generated Text")
            st.write(text)
            audio_path = generate_audio_from_text(text)
            st.markdown("## Audio Path")
            st.write(audio_path)

            drive_manager = FirebaseManager('x-reacts')
            audio_url = drive_manager.upload_file(audio_path, 'audio2.mp3')
            st.markdown("## Audio URL")
            st.write(audio_url)

            gen_video_path = generate_video_from_audio(audio_url)
            st.markdown("## Generated Video Path")
            st.write(gen_video_path)
            assemble_video(gen_video_path, path_to_video)
            st.markdown("## Processed Video")
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