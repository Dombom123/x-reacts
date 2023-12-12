from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip
import numpy as np
from moviepy.editor import concatenate_videoclips

def create_split_screen(avatar_video, original_video, position):
    avatar_resized = avatar_video.resize(height=original_video.h // 2)
    return CompositeVideoClip([original_video, avatar_resized.set_position(position)])

def create_full_screen(avatar_video, zoom=False):
    if zoom:
        avatar_zoomed = avatar_video.resize(lambda t: 1 + 0.5 * np.sin(t * 2 * np.pi / 5))
        return avatar_zoomed
    else:
        return avatar_video

def assemble_video(gen_path, original_video_path, audio_path):
    original_video = VideoFileClip(original_video_path)
    avatar_video = VideoFileClip(gen_path).subclip(0, original_video.duration)
    audio = AudioFileClip(audio_path)

    original_video = original_video.volumex(0.1)
    avatar_video = avatar_video.set_audio(audio)

    # Define time intervals (in seconds) for each template
    intervals = [(i, i+2) for i in range(0, int(original_video.duration), 2)]  # Modify as needed

    clips = []
    for i, (start, end) in enumerate(intervals):
        if i % 4 == 0:
            clip = create_split_screen(avatar_video.subclip(start, end), original_video.subclip(start, end), 'top')
        elif i % 4 == 1:
            clip = create_split_screen(avatar_video.subclip(start, end), original_video.subclip(start, end), 'bottom')
        elif i % 4 == 2:
            clip = create_full_screen(avatar_video.subclip(start, end))
        elif i % 4 == 3:
            clip = create_full_screen(avatar_video.subclip(start, end), zoom=True)
        
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile('final.mp4', codec='libx264', audio_codec='aac')

def main():
    gen_path = "avatar.mp4"
    original_video_path = "data/input.mp4"
    audio_path = "audio.mp3"
    assemble_video(gen_path, original_video_path, audio_path)

if __name__ == "__main__":
    main()
