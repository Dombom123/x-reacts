
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

import numpy as np



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
    composite_video.write_videofile('data/final.mp4')


def edit_video():

    input = VideoFileClip("data/input_video.mp4")
    avatar = VideoFileClip("data/avatar.mp4")
    

def main():
    gen_path = 'data/gen.mp4'
    original_video_path = 'data/original.mp4'
    audio_path = 'data/audio.mp3'
    assemble_video(gen_path, original_video_path, audio_path)
    print('Done')




if __name__ == '__main__':
    main()
