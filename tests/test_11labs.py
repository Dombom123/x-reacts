from elevenlabs import generate, Voice, VoiceSettings,set_api_key
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.editor import AudioFileClip, concatenate_audioclips
import numpy as np
from pydub import AudioSegment

import streamlit as st
 
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


def main():
    text = "Hello, my name is John. I am a software engineer at Eleven Labs. I am very happy to be here today to present this talk."
    generate_audio_from_text(text)

    prepend_silence('data/audio.mp3', 3)
    print('Done')

if __name__ == '__main__':
    main()