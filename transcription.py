# project/transcription.py
import os
import json
try:
    import whisper
except Exception as e:
    print("[ERROR] whisper is required. Install with: pip install -U openai-whisper")
    raise

from helpers import format_time_srt

def transcribe_video(video_path, temp_dir, model_size="medium"):
    print(f"[INFO] Transcribing {video_path} with model='{model_size}' (word-level timestamps)...")
    model = whisper.load_model(model_size)
    res = model.transcribe(video_path, word_timestamps=True)
    json_path = os.path.join(temp_dir, "transcription.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Transcription saved to: {json_path}")
    return json_path, res

def review_transcription(json_path, transcription):
    """Allow user to review and optionally edit segment-level text.
    NOTE: editing will not update per-word timestamps (if present)."""
    print("\n[REVIEW] Transcription segments (index: start - end : text)\n")
    for i, seg in enumerate(transcription.get('segments', [])):
        print(f"[{i}] {format_time_srt(seg.get('start',0))} - {format_time_srt(seg.get('end',0))}: {seg.get('text','').strip()}")

    edit = input('\nDo you want to edit any segment text? (y/n): ').strip().lower()
    if edit == 'y':
        while True:
            choice = input("Enter segment index to edit (or 'done' to finish): ").strip()
            if choice.lower() == 'done':
                break
            try:
                idx = int(choice)
                if 0 <= idx < len(transcription.get('segments', [])):
                    seg = transcription['segments'][idx]
                    print(f"Original: {seg.get('text','').strip()}")
                    new = input("New text (leave empty to keep original): ").strip()
                    if new:
                        transcription['segments'][idx]['text'] = new
                        print("[INFO] Segment updated.")
                else:
                    print("[ERROR] Index out of range.")
            except ValueError:
                print("[ERROR] Please enter a number or 'done'.")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Updated transcription saved: {json_path}")

    return json_path, transcription