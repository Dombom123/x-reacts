# X-Reacts: AI Video Processing
<img width="883" alt="header" src="https://github.com/Dombom123/x-reacts/assets/99609753/462c8840-f401-4744-b301-36cac88c61e2">

## Introduction
X-Reacts is a video processing tool using AI, ideal for transforming videos into more engaging content. This tool integrates various APIs for audio transcription, text generation, avatar creation, and video editing.

## Features
- Video Transcription using OpenAI's GPT-4
- Text-to-Speech via OpenAI
- Talking Avatars using D-ID API
- Video Editing with moviepy
- Streamlit-based interface

## Prerequisites
- Python 3.6 or higher
- Streamlit
- OpenAI and D-ID API access
- moviepy

## Installation
git clone [repository URL]
cd [repository directory]
pip install -r requirements.txt

## Environment Setup
To run the application, you need to set up your API keys. Rename the provided `secrets.toml.example` file to `secrets.toml` and insert your OpenAI and D-ID API keys:

# secrets.toml

[openai]
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

[d-id]
authorization = "YOUR_D-ID_AUTHORIZATION_KEY"

Make sure to replace `YOUR_OPENAI_API_KEY` and `YOUR_D-ID_AUTHORIZATION_KEY` with your actual API keys.

## Usage
1. Run `streamlit run app.py` in the terminal.
2. Upload a video through the web interface.
3. Choose or input a prompt.
4. Click 'Start generating' to process the video.

## How It Works
- Reads and processes video frames.
- Transcribes audio and generates text based on frames and prompts.
- Converts text to speech and generates avatars.
- Assembles the final video by combining original and generated content.

## Contributing
Contributions are welcome. Please follow these steps:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/YourFeature`)
3. Commit your Changes (`git commit -m 'Add some YourFeature'`)
4. Push to the Branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## License
This project is under the MIT License.

