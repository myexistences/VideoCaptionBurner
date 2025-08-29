# project/helpers.py
import os
import sys
import re
import subprocess
import json

def format_time_ass(t: float) -> str:
    """Format time for ASS (centiseconds precision): H:MM:SS.cc"""
    total_cs = int(round(t * 100))  # centiseconds
    cs = total_cs % 100
    total_seconds = total_cs // 100
    s = total_seconds % 60
    m = (total_seconds // 60) % 60
    h = total_seconds // 3600
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def format_time_srt(t: float) -> str:
    """Format time for SRT (milliseconds precision): HH:MM:SS,mmm"""
    total_ms = int(round(t * 1000))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    m = (total_seconds // 60) % 60
    h = total_seconds // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def normalize_hex_color_to_ass(hexstr: str) -> str:
    """Accepts formats like '#RRGGBB' or 'RRGGBB' or already ASS form '&H00BBGGRR' and
    returns ASS primary colour string like '&H00BBGGRR'. If input invalid returns default white.
    """
    if not hexstr:
        return "&H00FFFFFF"
    hexstr = hexstr.strip()
    if hexstr.startswith("&H"):
        if re.match(r"&H[0-9A-Fa-f]{8}$", hexstr):
            return hexstr
        return "&H00FFFFFF"
    m = re.match(r"#?([0-9A-Fa-f]{6})$", hexstr)
    if not m:
        return "&H00FFFFFF"
    rrggbb = m.group(1)
    rr = rrggbb[0:2]
    gg = rrggbb[2:4]
    bb = rrggbb[4:6]
    return f"&H00{bb}{gg}{rr}".upper()

def get_video_resolution(video_path):
    """Get video resolution using ffprobe (best-effort)."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        width = int(data['streams'][0]['width'])
        height = int(data['streams'][0]['height'])
        return width, height
    except Exception as e:
        print(f"[WARN] ffprobe failed to get resolution ({e}). Using 1920x1080 fallback.")
        return 1920, 1080