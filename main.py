# project/main.py
import os
import sys
from transcription import transcribe_video, review_transcription
from caption_builder import build_caption_units
from subtitle import get_user_font_choice, write_subtitles_files
from burner import burn_subtitles_ffmpeg
from helpers import get_video_resolution, normalize_hex_color_to_ass
from datetime import datetime
import json
import tempfile
import shutil

def create_and_burn(video_path, model_size='medium'):
    temp_dir = tempfile.mkdtemp(prefix='captions_')
    temp_files = []

    try:
        if not os.path.isfile(video_path):
            print('[ERROR] Video file not found:', video_path)
            return

        # Ask thresholds (ms) so user can override defaults
        try:
            print("\n[PAUSE THRESHOLDS in milliseconds]")
            default_continue_ms = 200
            default_separate_ms = 600
            cont_ms_in = input(f"Continue same line if gap < ms (default {default_continue_ms}): ").strip()
            sep_ms_in = input(f"Treat gap >= ms as separate caption (vanish) (default {default_separate_ms}): ").strip()
            continue_if_gap_ms = int(cont_ms_in) if cont_ms_in else default_continue_ms
            separate_if_gap_ms = int(sep_ms_in) if sep_ms_in else default_separate_ms
            if separate_if_gap_ms <= continue_if_gap_ms:
                print("[WARN] separate threshold must be > continue threshold; using defaults.")
                continue_if_gap_ms = default_continue_ms
                separate_if_gap_ms = default_separate_ms
        except Exception:
            continue_if_gap_ms = default_continue_ms
            separate_if_gap_ms = default_separate_ms

        output_dir = os.path.dirname(video_path) or os.getcwd()
        resolution = get_video_resolution(video_path)

        json_path, transcription = transcribe_video(video_path, temp_dir, model_size=model_size)
        json_path, transcription = review_transcription(json_path, transcription)

        # ---------------- FONT CHOICE ----------------
        font_name, font_path = get_user_font_choice()

        # Caption style defaults. Ask user for vertical placement
        width, height = resolution
        default_font_size = int(max(24, height * 0.05))
        print('\n[STYLE] Caption styling configuration (press Enter to accept default)')
        font_size_input = input(f"Font size in px (default {default_font_size}): ").strip()
        try:
            font_size = int(font_size_input) if font_size_input else default_font_size
        except Exception:
            font_size = default_font_size

        font_color = input("Font color hex (e.g. #FFFFFF) [#FFFFFF]: ").strip() or "#FFFFFF"
        outline_color = input("Outline color hex (e.g. #000000) [#000000]: ").strip() or "#000000"

        print("Position options: bottom, lower-center, center, top")
        position = input("Choose position [bottom]: ").strip() or "bottom"

        shadow = input("Shadow size (pixels) [2]: ").strip() or '2'
        try:
            shadow = float(shadow)
        except Exception:
            shadow = 2.0

        style = {
            'font_name': font_name,
            'font_path': font_path,
            'font_size': font_size,
            'font_color': font_color,
            'outline_color': outline_color,
            'position': position,
            'shadow': shadow
        }

        # Build captions with user-controlled thresholds
        captions = build_caption_units(
            transcription,
            max_words_per_line=5,
            max_words_per_caption=4,
            continue_if_gap_ms=continue_if_gap_ms,
            separate_if_gap_ms=separate_if_gap_ms
        )

        if not captions:
            print('[ERROR] No captions built')
            return

        parsed_json = os.path.join(temp_dir, 'captions_parsed.json')
        with open(parsed_json, 'w', encoding='utf-8') as pj:
            json.dump(captions, pj, ensure_ascii=False, indent=2)
        temp_files.append(parsed_json)

        # Write SRT/ASS
        srt_path, ass_path = write_subtitles_files(captions, style, resolution, temp_dir)
        temp_files.extend([srt_path, ass_path])

        # Burn subtitles
        output_video = burn_subtitles_ffmpeg(video_path, ass_path, srt_path, output_dir, temp_dir, style)
        print('[DONE] Output video:', output_video)

    finally:
        for p in temp_files:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

def main():
    print('=== Enhanced Caption Burner (BY @myexistences) ===')
    while True:
        video_path = input('Enter full path to video file (or type quit to exit): ').strip('"')
        if not video_path:
            continue
        if video_path.lower() in ('q', 'quit', 'exit'):
            break
        model_size = input("Whisper model size (tiny, base, small, medium, large) [medium]: ").strip() or 'medium'
        try:
            create_and_burn(video_path, model_size=model_size)
        except Exception as e:
            print(f"[ERROR] Failed: {e}")

        again = input('Process another file? (y/n): ').strip().lower() or 'n'
        if again != 'y':
            break

if __name__ == '__main__':
    main()
