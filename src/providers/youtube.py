"""YouTube provider — fetches transcript via youtube-transcript-api."""

import re


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _seg_to_dict(seg) -> dict:
    if isinstance(seg, dict):
        return seg
    return {"text": seg.text, "start": seg.start, "duration": seg.duration}


class YouTubeProvider:
    name = "youtube"
    display_name = "YouTube"
    link_text = "🎥 Assistir no YouTube"

    def detect(self, url: str) -> bool:
        return bool(re.search(r'(youtube\.com|youtu\.be)', url))

    def extract_id(self, url: str) -> str:
        url = url.strip()
        for pattern in [
            r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$',
        ]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url

    def fetch_transcript(self, url: str, timestamps: bool = True) -> str:
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = self.extract_id(url)

        try:
            ytt = YouTubeTranscriptApi()
            try:
                raw = ytt.fetch(video_id)
            except Exception:
                transcript_list = ytt.list(video_id)
                transcript = None
                for t in transcript_list:
                    transcript = t
                    break
                if transcript is None:
                    raise RuntimeError(f"Nenhuma transcrição encontrada para {video_id}")
                raw = transcript.fetch()
        except AttributeError:
            raw = YouTubeTranscriptApi.get_transcript(video_id)

        segments = [_seg_to_dict(s) for s in raw]

        if timestamps:
            return "\n".join(
                f"{_format_timestamp(seg['start'])} {seg['text']}" for seg in segments
            )
        return " ".join(seg["text"] for seg in segments)
