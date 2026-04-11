#!/usr/bin/env python3
"""
Extract presentation slides from a video.

Strategy: sample frames at regular intervals, compare consecutive frames
using histogram difference, and keep frames where significant visual change occurred.
This works better than ffmpeg scene detection for screen recordings and presentations
with smooth transitions.

Usage (standalone):
    python3 scripts/extract_slides.py /tmp/video.mp4 img/my-slug/ [--interval 2] [--threshold 0.3]
"""

import json
import os
import subprocess
import sys

MAX_SLIDES = 60


def _format_ts(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def _get_duration(video_path: str) -> float:
    """Get video duration in seconds via ffprobe."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return float(result.stdout.strip())


def _extract_frames_at_interval(video_path: str, output_dir: str, interval: float = 2.0):
    """Extract one frame every N seconds as JPEG. Returns list of (timestamp, filepath)."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame-%06d.jpg")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval},scale='min(1280,iw)':-1",
        "-q:v", "3",
        pattern,
        "-y",
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Collect generated frames with their timestamps
    frames = []
    i = 1
    while True:
        path = os.path.join(output_dir, f"frame-{i:06d}.jpg")
        if not os.path.exists(path):
            break
        ts = (i - 1) * interval
        frames.append({"timestamp": ts, "path": path})
        i += 1

    return frames


def _compare_frames(path_a: str, path_b: str) -> float:
    """
    Compare two images using pixel-level mean absolute difference on the slide region.
    Crops to the right 60% of the frame to ignore webcam overlays.
    Returns 0.0 (completely different) to 1.0 (identical).
    """
    try:
        import cv2
        import numpy as np
        img_a = cv2.imread(path_a, cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imread(path_b, cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 1.0

        # Crop to right 60% to focus on slide area (ignore webcam overlay)
        h, w = img_a.shape
        crop_x = int(w * 0.4)
        a = img_a[:, crop_x:]
        b = img_b[:, crop_x:]

        # Resize to same dimensions if needed
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))

        # Mean absolute difference normalized to [0,1]
        diff = np.mean(np.abs(a.astype(float) - b.astype(float))) / 255.0
        return 1.0 - diff
    except ImportError:
        try:
            size_a = os.path.getsize(path_a)
            size_b = os.path.getsize(path_b)
            if size_a == 0:
                return 1.0
            return 1.0 - min(abs(size_a - size_b) / size_a, 1.0)
        except OSError:
            return 1.0


def extract_slides(video_path: str, output_dir: str,
                   interval: float = 2.0, threshold: float = 0.85) -> list[dict]:
    """
    Extract distinct slides from a video.

    1. Sample frames every `interval` seconds
    2. Compare consecutive frames via histogram
    3. Keep frames where similarity < threshold (= slide changed)
    4. Always keep the first frame

    Returns list of {"timestamp": float, "filename": str}.
    """
    print(f"  Extraindo frames a cada {interval}s...")
    frames = _extract_frames_at_interval(video_path, output_dir, interval)
    if not frames:
        return []

    print(f"  {len(frames)} frames extraídos, detectando mudanças de slide...")

    # Always keep first frame
    kept = [frames[0]]

    for i in range(1, len(frames)):
        similarity = _compare_frames(frames[i - 1]["path"], frames[i]["path"])
        if similarity < threshold:
            kept.append(frames[i])

    # Rename kept frames as slide-NNNN.jpg, delete the rest
    slides = []
    kept_paths = set()
    for i, frame in enumerate(kept):
        new_name = f"slide-{i+1:04d}.jpg"
        new_path = os.path.join(output_dir, new_name)
        if frame["path"] != new_path:
            os.rename(frame["path"], new_path)
        kept_paths.add(new_name)
        slides.append({"timestamp": frame["timestamp"], "filename": new_name})

    # Cleanup unused frames
    for f in os.listdir(output_dir):
        if f.startswith("frame-") or (f.startswith("slide-") and f not in kept_paths):
            try:
                os.remove(os.path.join(output_dir, f))
            except OSError:
                pass

    # Cap at MAX_SLIDES — keep evenly spaced subset
    if len(slides) > MAX_SLIDES:
        step = len(slides) / MAX_SLIDES
        subset = [slides[int(i * step)] for i in range(MAX_SLIDES)]
        # Cleanup extras
        subset_files = {s["filename"] for s in subset}
        for s in slides:
            if s["filename"] not in subset_files:
                try:
                    os.remove(os.path.join(output_dir, s["filename"]))
                except OSError:
                    pass
        slides = subset

    return slides


def build_slides_json(slides: list[dict], segments: list[dict], slug: str, output_path: str):
    """
    Correlate slides with transcript segments by timestamp.
    Writes JSON with [{timestamp, timestamp_fmt, path, nearest_text}].
    """
    result = []
    for slide in slides:
        ts = slide["timestamp"]
        nearest_text = ""
        min_diff = float("inf")
        for seg in segments:
            diff = abs(seg["start"] - ts)
            if diff < min_diff:
                min_diff = diff
                nearest_text = seg["text"].strip()
        result.append({
            "timestamp": ts,
            "timestamp_fmt": _format_ts(ts),
            "path": f"img/{slug}/{slide['filename']}",
            "nearest_text": nearest_text,
        })

    with open(output_path, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract slides from video")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("output_dir", help="Output directory for slide images")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between samples (default: 2)")
    parser.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold (default: 0.85)")
    args = parser.parse_args()

    slides = extract_slides(args.video, args.output_dir, args.interval, args.threshold)
    print(f"\nExtracted {len(slides)} slides to {args.output_dir}")
    for s in slides:
        print(f"  {_format_ts(s['timestamp'])} → {s['filename']}")
