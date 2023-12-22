import subprocess
import streamlit as st

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

def main():
    url = st.text_input('Enter a YouTube video URL')
    if st.button('Download'):
        download_video(url)
        st.video('data/input.mp4')
    
if __name__ == '__main__':
    main()