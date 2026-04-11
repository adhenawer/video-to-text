"""Twitter/X provider — downloads audio via yt-dlp, transcribes via mlx-whisper."""

import glob
import os
import re
import subprocess
import sys

WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class TwitterProvider:
    name = "twitter"
    display_name = "Twitter/X"
    link_text = "🐦 Ver no Twitter/X"

    def detect(self, url: str) -> bool:
        return bool(re.search(r'(twitter\.com|x\.com)/\w+/status/\d+', url))

    def extract_id(self, url: str) -> str:
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Não foi possível extrair tweet ID de: {url}")

    def fetch_transcript(self, url: str, timestamps: bool = True) -> str:
        tweet_id = self.extract_id(url)
        audio_path = f"/tmp/twitter_audio_{tweet_id}.m4a"

        try:
            self._download_audio(url, tweet_id, audio_path)
            text = self._transcribe(audio_path, timestamps)
        finally:
            # Cleanup temp audio files
            for f in glob.glob(f"/tmp/twitter_audio_{tweet_id}*"):
                try:
                    os.remove(f)
                except OSError:
                    pass

        return text

    def _download_audio(self, url: str, tweet_id: str, output_path: str):
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-x",
            "--audio-format", "m4a",
            "--audio-quality", "0",
            "--no-playlist",
            "-o", output_path,
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp falhou: {result.stderr.strip()}")

        # yt-dlp may produce file with different extension — find it
        if not os.path.exists(output_path):
            candidates = glob.glob(f"/tmp/twitter_audio_{tweet_id}.*")
            if candidates:
                os.rename(candidates[0], output_path)
            else:
                raise RuntimeError("yt-dlp não produziu arquivo de áudio. Vídeo pode não ter áudio.")

        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Arquivo de áudio vazio. Vídeo pode não ter faixa de áudio.")

    def _transcribe(self, audio_path: str, timestamps: bool) -> str:
        import mlx_whisper

        print(f"  Transcrevendo áudio com Whisper ({WHISPER_MODEL})...")
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=WHISPER_MODEL,
            word_timestamps=False,
        )

        segments = result.get("segments", [])
        if not segments:
            raise RuntimeError("Whisper não produziu segmentos. Áudio pode estar silencioso ou corrompido.")

        if timestamps:
            lines = []
            for seg in segments:
                text = seg['text'].strip()
                if text:
                    lines.append(f"{_format_timestamp(seg['start'])} {text}")
            return "\n".join(lines)
        return " ".join(seg["text"].strip() for seg in segments if seg["text"].strip())
