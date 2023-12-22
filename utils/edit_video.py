from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, TextClip
import numpy as np



def create_split_screen(avatar_video, original_video, position):
    # Resize the avatar video to match the width of the original video
    scale_factor_width = original_video.w / avatar_video.w
    avatar_resized = avatar_video.resize(newsize=(original_video.w, int(avatar_video.h * scale_factor_width)))

    # Crop the avatar video to half of the original video's height
    if avatar_resized.h > original_video.h / 2:
        avatar_resized = avatar_resized.crop(y_center=avatar_resized.h / 2, height=original_video.h // 2)

    # Adjust the position of both videos
    if position == 'top':
        avatar_y_pos = 0
        original_y_pos = original_video.h // 2
    else:
        avatar_y_pos = original_video.h // 2
        original_y_pos = 0

    # Position avatar video and original video
    avatar_clip = avatar_resized.set_position(('center', avatar_y_pos))
    original_clip = original_video.set_position(('center', original_y_pos))

    return CompositeVideoClip([original_clip, avatar_clip], size=original_video.size)


def create_full_screen(avatar_video, original_video, zoom=0):
    if zoom == 1:
        # Resize avatar video to the original video size with zoom effect
        avatar_zoomed = avatar_video.set_position('center').resize(height=original_video.h*1.25)
        return CompositeVideoClip([avatar_zoomed], size=original_video.size)
    if zoom == 2:
        # Resize avatar video to the original video size with zoom effect
        avatar_zoomed = avatar_video.set_position('center').resize(height=original_video.h*1.5)
        return CompositeVideoClip([avatar_zoomed], size=original_video.size)
    else:
        # Resize avatar video to match the original video's size
        avatar_resized = avatar_video.set_position('center').resize(height=original_video.h)

        return CompositeVideoClip([avatar_resized], size=original_video.size)



def assemble_video(gen_path, original_video_path, audio_path):
    original_video = VideoFileClip(original_video_path).volumex(0.2)
    avatar_video = VideoFileClip(gen_path)
    audio = AudioFileClip(audio_path).subclip(0, avatar_video.duration)

    if original_video.duration < avatar_video.duration:
        loops = int(np.ceil(avatar_video.duration / original_video.duration))
        original_video = concatenate_videoclips([original_video] * loops).subclip(0, avatar_video.duration)

    avatar_video = avatar_video.set_audio(audio)

    # Define the sequence of clips as functions and their parameters
    sequence_patterns = [
        (create_split_screen, {'position': 'bottom'}),
        (create_split_screen, {'position': 'bottom'}),
        (create_full_screen, {'zoom': 0}),
        (create_full_screen, {'zoom': 1}),
        (create_split_screen, {'position': 'top'}),
        (create_split_screen, {'position': 'top'}),
        (create_full_screen, {'zoom': 1}),
        (create_full_screen, {'zoom': 2}),
        (create_full_screen, {'zoom': 1}),
        (create_full_screen, {'zoom': 2}),
        (create_full_screen, {'zoom': 0})
    ]

    # Define intervals
    intervals = [(i, min(i+3, avatar_video.duration)) for i in range(0, int(avatar_video.duration), 3)]
    clips = []
    # print(TextClip.list('font'))
    # Create a text clip
    # txt_clip = TextClip("Reactions from Hell", fontsize=60, font='Helvetica-Neue-Condensed-Bold', color='white', bg_color='black')
    # txt_clip = txt_clip.set_pos('center').set_duration(3)  # Set duration to match first clip

    # # Overlay the text clip on the first video clip
    # first_clip_func, first_clip_params = sequence_patterns[0]
    # first_clip = first_clip_func(avatar_video.subclip(0, 3), original_video.subclip(0, 3), **first_clip_params)
    # first_clip_with_text = CompositeVideoClip([first_clip, txt_clip])

    # # Replace the first clip in the sequence with the new clip with text
    # clips = [first_clip_with_text]

    # Iterate over the remaining intervals and sequence patterns
    for i, (start, end) in enumerate(intervals):  # Start from the second interval
        func, params = sequence_patterns[(i + 1) % len(sequence_patterns)]
        clip = func(avatar_video.subclip(start, end), original_video.subclip(start, end), **params)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile('data/final.mp4', codec='libx264', audio_codec='aac')
def main():
    gen_path = "data/avatar.mp4"
    original_video_path = "data/input.mp4"
    audio_path = "data/audio.mp3"
    assemble_video(gen_path, original_video_path, audio_path)

if __name__ == "__main__":
    main()