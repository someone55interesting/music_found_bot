# services/downloader.py

import os
from yt_dlp import YoutubeDL
from config import TEMP_DIR, MP3_BITRATE


def download_mp3(video_id: str) -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)

    output_template = os.path.join(TEMP_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": MP3_BITRATE.replace("k", ""),
            }
        ],
    }

    url = f"https://www.youtube.com/watch?v={video_id}"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_file = filename.rsplit(".", 1)[0] + ".mp3"

    return mp3_file
