import yt_dlp
import os
import asyncio
from pathlib import Path
from config import TEMP_DIR, MAX_FILE_SIZE_MB


class VideoDownloader:

    QUALITY_MAP = {
        "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]",
        "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]",
        "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]",
        "audio": "bestaudio[ext=m4a]/bestaudio",
    }

    def get_ydl_opts(self, quality: str, output_path: str) -> dict:
        return {
            "format": self.QUALITY_MAP.get(quality, self.QUALITY_MAP["best"]),
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
            "extractor_args": {"tiktok": {"webpage_download": ["1"]}},
            "max_filesize": MAX_FILE_SIZE_MB * 1024 * 1024,
        }

    async def get_info(self, url: str) -> dict:
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        loop = asyncio.get_event_loop()
        def _extract():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        return await loop.run_in_executor(None, _extract)

    async def download(self, url: str, quality: str, file_id: str) -> str:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = f"{TEMP_DIR}/{file_id}.%(ext)s"
        opts = self.get_ydl_opts(quality, output_path)
        loop = asyncio.get_event_loop()
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        await loop.run_in_executor(None, _download)
        for f in Path(TEMP_DIR).glob(f"{file_id}.*"):
            return str(f)
        raise FileNotFoundError("فشل التحميل")
