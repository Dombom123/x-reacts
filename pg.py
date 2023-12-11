import requests

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
        "audio_url": "s3://d-id-audios-prod/auth0|6492c97ee4e1f79e8cb57cfa/DUV9kvHxFIcYB6Dbt51Hq/audio.wav",
        "reduce_noise": True
    },
    "config": {
        "fluent": True,
        "pad_audio": 5,
        "stitch": True,
        "result_format": "mp4",
        "sharpen": True
    },
    "source_url": "https://i.ibb.co/b6S8DYJ/Bildschirmfoto-2023-11-17-um-10-22-22-removebg-preview.png"
}
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Basic YUdGdWJtVnpRR1J5YVhabFltVjBZUzVrWlE6THp3WUcyVXhwVTQzUzhKZXluaHA3"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)