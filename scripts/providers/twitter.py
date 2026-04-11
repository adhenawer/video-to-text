"""Twitter/X provider — downloads audio via yt-dlp, transcribes via mlx-whisper."""

import glob
import json
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

    def fetch_transcript(self, url: str, timestamps: bool = True,
                         slides: bool = False, slides_dir: str = None,
                         slug: str = None) -> str:
        tweet_id = self.extract_id(url)
        video_path = f"/tmp/twitter_video_{tweet_id}.mp4"
        audio_path = f"/tmp/twitter_audio_{tweet_id}.m4a"

        try:
            if slides:
                # Download full video, extract audio from it
                self._download_video(url, tweet_id, video_path)
                self._extract_audio_from_video(video_path, audio_path)
            else:
                self._download_audio(url, tweet_id, audio_path)

            text, segments = self._transcribe(audio_path, timestamps, return_segments=True)

            # Save segments JSON for slide correlation
            segments_path = f"/tmp/{tweet_id}_segments.json"
            with open(segments_path, "w") as f:
                json.dump(segments, f, ensure_ascii=False)

            # Extract slides if requested
            if slides and slides_dir and slug:
                from extract_slides import extract_slides, build_slides_json
                print(f"  Extraindo slides do vídeo (threshold padrão)...")
                slide_list = extract_slides(video_path, slides_dir)
                print(f"  {len(slide_list)} slides extraídos")
                slides_json_path = f"/tmp/{tweet_id}_slides.json"
                build_slides_json(slide_list, segments, slug, slides_json_path)

        finally:
            # Cleanup temp files (keep slides dir and JSON)
            for pattern in [f"/tmp/twitter_video_{tweet_id}*",
                            f"/tmp/twitter_audio_{tweet_id}*"]:
                for f in glob.glob(pattern):
                    try:
                        os.remove(f)
                    except OSError:
                        pass

        return text

    def _download_video(self, url: str, tweet_id: str, output_path: str):
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "best[ext=mp4]/best",
            "--no-playlist",
            "-o", output_path,
            url,
        ]
        print(f"  Baixando vídeo completo...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp (vídeo) falhou: {result.stderr.strip()}")

        if not os.path.exists(output_path):
            candidates = glob.glob(f"/tmp/twitter_video_{tweet_id}.*")
            if candidates:
                os.rename(candidates[0], output_path)
            else:
                raise RuntimeError("yt-dlp não produziu arquivo de vídeo.")

    def _extract_audio_from_video(self, video_path: str, audio_path: str):
        cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "aac", "-y", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg extração áudio falhou: {result.stderr.strip()}")

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp falhou: {result.stderr.strip()}")

        if not os.path.exists(output_path):
            candidates = glob.glob(f"/tmp/twitter_audio_{tweet_id}.*")
            if candidates:
                os.rename(candidates[0], output_path)
            else:
                raise RuntimeError("yt-dlp não produziu arquivo de áudio. Vídeo pode não ter áudio.")

        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Arquivo de áudio vazio. Vídeo pode não ter faixa de áudio.")

    def _transcribe(self, audio_path: str, timestamps: bool,
                    return_segments: bool = False):
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

        # Build raw segments list for JSON export
        raw_segments = [{"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                        for s in segments if s["text"].strip()]

        if timestamps:
            lines = []
            for seg in segments:
                text = seg['text'].strip()
                if text:
                    lines.append(f"{_format_timestamp(seg['start'])} {text}")
            text_output = "\n".join(lines)
        else:
            text_output = " ".join(seg["text"].strip() for seg in segments if seg["text"].strip())

        if return_segments:
            return text_output, raw_segments
        return text_output
