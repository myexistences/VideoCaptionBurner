#!/usr/bin/env python3
"""
Enhanced video captioning tool
- Lists installed fonts and lets you choose one (if matplotlib is available it will list friendly names)
- Uses Whisper for transcription with word timestamps
- Saves per-word timestamps (millisecond precision) in the transcription JSON
- Builds subtitle captions that:
  * split on short pauses (configurable)
  * limit a single line to a maximum of 5 words by default
  * allow up to two lines per caption (10 words total by default)
- Writes both SRT (millisecond timestamps) and ASS (styled) subtitle files
- Burns captions into the video using FFmpeg (tries ASS/libass first, then falls back to subtitles filter)

Usage: python caption_burner_enhanced.py
Requires: whisper, ffmpeg available in PATH. Optional: matplotlib, fonttools for better font listing.
Install with: pip install -U openai-whisper matplotlib fonttools
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import shlex
import re
from datetime import datetime

try:
    import whisper
except Exception as e:
    print("[ERROR] whisper is required. Install with: pip install -U openai-whisper")
    raise


# ------------------------- Helpers for time formatting -------------------------

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


# ------------------------- Font discovery -------------------------

def get_installed_fonts(limit_list=200):
    """Try to return a list of installed font names. Best-effort, cross-platform.
    Tries matplotlib.font_manager first (gives friendly names). If not available it
    will try fonttools to read TTF names. As last resort, returns font file basenames
    from common font directories.
    """
    fonts = []
    try:
        from matplotlib import font_manager
        fonts = sorted({f.name for f in font_manager.fontManager.ttflist})
        if fonts:
            return fonts[:limit_list]
    except Exception:
        pass

    # fallback: search common font directories
    common_dirs = []
    if sys.platform.startswith("win"):
        common_dirs = [r"C:\Windows\Fonts"]
    elif sys.platform == "darwin":
        common_dirs = ["/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
    else:
        # linux/unix
        common_dirs = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")] 

    font_files = []
    for d in common_dirs:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for fn in files:
                    if fn.lower().endswith((".ttf", ".otf", ".ttc")):
                        font_files.append(os.path.join(root, fn))

    # try fontTools to extract the real name
    try:
        from fontTools.ttLib import TTFont
        names = []
        for fpath in font_files:
            try:
                tt = TTFont(fpath, fontNumber=0, ignoreDecompileErrors=True)
                for record in tt['name'].names:
                    if record.nameID == 1:
                        try:
                            name = record.toUnicode()
                        except Exception:
                            name = record.string.decode('utf-8', errors='ignore')
                        if name:
                            names.append(name)
                            break
            except Exception:
                continue
        if names:
            return sorted(set(names))[:limit_list]
    except Exception:
        # unable to parse font files; fall back to filenames
        pass

    # last resort: use file basenames
    names = [os.path.splitext(os.path.basename(p))[0] for p in font_files]
    return sorted(set(names))[:limit_list]


# ------------------------- Color helpers -------------------------

def normalize_hex_color_to_ass(hexstr: str) -> str:
    """Accepts formats like '#RRGGBB' or 'RRGGBB' or already ASS form '&H00BBGGRR' and
    returns ASS primary colour string like '&H00BBGGRR'. If input invalid returns default white.
    """
    if not hexstr:
        return "&H00FFFFFF"
    hexstr = hexstr.strip()
    if hexstr.startswith("&H"):
        # assume user supplied ASS colour
        if re.match(r"&H[0-9A-Fa-f]{8}$", hexstr):
            return hexstr
        return "&H00FFFFFF"
    # allow #RRGGBB or RRGGBB
    m = re.match(r"#?([0-9A-Fa-f]{6})$", hexstr)
    if not m:
        return "&H00FFFFFF"
    rrggbb = m.group(1)
    rr = rrggbb[0:2]
    gg = rrggbb[2:4]
    bb = rrggbb[4:6]
    # ASS wants BBGGRR with optional alpha first (we use 00 alpha)
    return f"&H00{bb}{gg}{rr}".upper()


# ------------------------- Build captions from word timestamps -------------------------

def build_caption_units(data, max_words_per_line=5, max_words_per_caption=10, pause_threshold=0.14):
    """
    Build caption chunks with:
      - stronger punctuation split,
      - single-word lines only for interjections/short words with punctuation,
      - preserve immediate start (start = first word start),
      - prefer natural phrases up to max_words_per_caption.
    """
    captions = []

    def flush(curr):
        if not curr:
            return
        start = curr[0][1]
        end = curr[-1][2]
        words = [w for (w, s, e) in curr]
        # split into lines (max_words_per_line)
        lines = []
        for i in range(0, len(words), max_words_per_line):
            lines.append(' '.join(words[i:i + max_words_per_line]))
        captions.append({
            'start': float(start),
            'end': float(end),
            'text_ass': '\\\\N'.join(lines),
            'text_srt': '\\n'.join(lines),
            'words': list(curr)
        })

    current = []
    last_end = None

    any_words = any('words' in seg and seg['words'] for seg in data.get('segments', []))
    if not any_words:
        # fallback: distribute segment timestamps evenly (keeps older behavior)
        for seg in data.get('segments', []):
            seg_text = seg.get('text', '').strip()
            if not seg_text:
                continue
            seg_start = float(seg.get('start', 0.0))
            seg_end = float(seg.get('end', seg_start))
            seg_words = [w for w in re.split(r"\s+", seg_text) if w]
            if not seg_words:
                continue
            per_word = (seg_end - seg_start) / max(1, len(seg_words))
            for i, w in enumerate(seg_words):
                s = seg_start + i * per_word
                e = s + per_word
                gap = 0 if last_end is None else s - last_end
                if gap >= pause_threshold or len(current) >= max_words_per_caption:
                    flush(current)
                    current = []
                current.append((w, s, e))
                last_end = e
        flush(current)
        return captions

    for seg in data.get('segments', []):
        for w in seg.get('words', []):
            word_text = (w.get('word') or '').strip()
            if not word_text:
                continue
            try:
                w_start = float(w.get('start', 0.0))
                w_end = float(w.get('end', w_start))
            except Exception:
                continue

            gap = 0 if last_end is None else (w_start - last_end)

            # heuristics
            ends_with_strong = bool(re.search(r'[\.!\?]$', word_text))
            is_short_interj = len(word_text) <= 5 and bool(re.search(r'[!?]$', word_text))

            # flush before adding if large gap or reached caption size
            if gap >= pause_threshold or len(current) >= max_words_per_caption:
                flush(current)
                current = []

            # if single short interjection with punctuation -> emit as single-word caption
            if is_short_interj and (gap >= 0.05 or ends_with_strong):
                # flush previous, emit this single, flush it
                flush(current)
                current = [(word_text, w_start, w_end)]
                flush(current)
                current = []
            else:
                current.append((word_text, w_start, w_end))
                # If strong punctuation on this word, flush (end of sentence)
                if ends_with_strong:
                    flush(current)
                    current = []

            last_end = w_end

    flush(current)
    return captions



# ------------------------- Create SRT and ASS files -------------------------

def write_subtitles_files(captions, style, resolution, temp_dir, base_name="captions"):
    """Write captions.srt and captions.ass into temp_dir and return their paths."""
    width, height = resolution
    srt_path = os.path.join(temp_dir, f"{base_name}.srt")
    ass_path = os.path.join(temp_dir, f"{base_name}.ass")

    # SRT
    with open(srt_path, "w", encoding="utf-8") as srt:
        for i, c in enumerate(captions, start=1):
            srt.write(f"{i}\n")
            srt.write(f"{format_time_srt(c['start'])} --> {format_time_srt(c['end'])}\n")
            srt.write(c['text_srt'] + "\n\n")

    # ASS header and style
    primary_color = normalize_hex_color_to_ass(style.get('font_color'))
    outline_color = normalize_hex_color_to_ass(style.get('outline_color'))
    font_name = style.get('font_name', 'Arial')
    font_size = int(style.get('font_size', max(24, int(height * 0.05))))
    pos = style.get('position', 2)
    shadow = float(style.get('shadow', 2))

    with open(ass_path, 'w', encoding='utf-8') as ass:
        ass.write("[Script Info]\n")
        ass.write("ScriptType: v4.00+\n")
        ass.write(f"PlayResX: {width}\n")
        ass.write(f"PlayResY: {height}\n\n")

        ass.write("[V4+ Styles]\n")
        ass.write("Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # BackColour keep semi-transparent black
        back = "&H64000000"
        # Outline numeric fields: Outline, Shadow
        ass.write(f"Style: MyStyle,{font_name},{font_size},{primary_color},{outline_color},{back},0,0,1,2,{shadow},{pos},20,20,40,0\n\n")

        ass.write("[Events]\n")
        ass.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for c in captions:
            ass_text = c['text_ass']
            # ASS times are centisecond-precision; they come from format_time_ass
            ass.write(f"Dialogue: 0,{format_time_ass(c['start'])},{format_time_ass(c['end'])},MyStyle,,0,0,0,,{ass_text}\n")

    return srt_path, ass_path


# ------------------------- FFmpeg burn-in -------------------------

def burn_subtitles_ffmpeg(video_path, ass_path, srt_path, output_dir, temp_dir):
    """
    Burns captions into the video. Prioritizes using SRT+fontsdir (preserves ms precision
    and forces libass to use the copied font file). Falls back to ASS (system lookup)
    then to SRT without fontsdir.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"captioned_{timestamp}.mp4")
    print(f"[INFO] Burning captions into video: {output_path}")

    current_dir = os.getcwd()
    try:
        temp_video = os.path.join(temp_dir, "video.mp4")
        shutil.copy(video_path, temp_video)
        os.chdir(temp_dir)
        temp_output = "output.mp4"

        # Get chosen font path from LAST_STYLE (set by create_and_burn)
        style = globals().get('LAST_STYLE') if isinstance(globals().get('LAST_STYLE'), dict) else None
        fonts_dir = None
        if style and style.get('font_path') and os.path.isfile(style.get('font_path')):
            fonts_dir = os.path.join(temp_dir, 'fonts')
            os.makedirs(fonts_dir, exist_ok=True)
            try:
                shutil.copy(style.get('font_path'), fonts_dir)
                print(f"[INFO] Copied font to fontsdir: {fonts_dir}")
            except Exception as e:
                print(f"[WARN] Could not copy font file to fontsdir: {e}")

        # 1) Try SRT + fontsdir (preferred — ms precision + fontsdir forces correct font file)
        if fonts_dir:
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "info",
                "-i", "video.mp4",
                "-vf", f"subtitles={shlex.quote(os.path.basename(srt_path))}:fontsdir={shlex.quote(fonts_dir)}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "copy", "-y", temp_output
            ]
            print(f"[DEBUG] Running (SRT+fontsdir): {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
                shutil.move(temp_output, output_path)
                print(f"[INFO] Final video saved (SRT+fontsdir): {output_path}")
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"[WARN] SRT+fontsdir failed: {e}. Trying ASS...")

        # 2) Try ASS (system lookup) — libass might find system-installed font by name
        cmd2 = [
            "ffmpeg", "-hide_banner", "-loglevel", "info",
            "-i", "video.mp4",
            "-vf", f"ass={shlex.quote(os.path.basename(ass_path))}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "copy", "-y", temp_output
        ]
        print(f"[DEBUG] Running (ASS): {' '.join(cmd2)}")
        try:
            subprocess.run(cmd2, check=True)
            shutil.move(temp_output, output_path)
            print(f"[INFO] Final video saved (ASS): {output_path}")
            return output_path
        except subprocess.CalledProcessError:
            print("[WARN] ASS filter failed; falling back to SRT without fontsdir.")

        # 3) Final fallback: SRT without fontsdir
        cmd3 = [
            "ffmpeg", "-hide_banner", "-loglevel", "info",
            "-i", "video.mp4",
            "-vf", f"subtitles={shlex.quote(os.path.basename(srt_path))}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy", "-y", temp_output
        ]
        print(f"[DEBUG] Running (SRT fallback): {' '.join(cmd3)}")
        subprocess.run(cmd3, check=True)
        shutil.move(temp_output, output_path)
        print(f"[INFO] Final video saved (SRT fallback): {output_path}")
        return output_path

    finally:
        os.chdir(current_dir)
        # cleanup temp copies
        try:
            if os.path.exists(temp_video):
                os.remove(temp_video)
        except Exception:
            pass
        try:
            if os.path.exists("output.mp4"):
                os.remove("output.mp4")
        except Exception:
            pass




# ------------------------- Existing utility functions -------------------------

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


def transcribe_video(video_path, temp_dir, model_size="medium"):
    print(f"[INFO] Transcribing {video_path} with model='{model_size}' (word-level timestamps)...")
    model = whisper.load_model(model_size)
    # whisper returns 'segments' with 'words' when word_timestamps=True in some builds. If not present, we still get segments.
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


# ------------------------- CLI / main flow -------------------------

def get_user_style_choices(resolution):
    width, height = resolution
    default_font_size = int(max(18, height * 0.05))
    print('\n[STYLE] Caption styling configuration')

    # Try to enumerate installed fonts (friendly names) using matplotlib if available
    fonts = []
    font_map = {}
    try:
        from matplotlib import font_manager
        entries = sorted(font_manager.fontManager.ttflist, key=lambda x: x.name)
        for e in entries:
            if e.name and os.path.isfile(e.fname):
                fonts.append(e.name)
                font_map[e.name] = e.fname
    except Exception:
        pass

    src = input("Choose font source: (1) Installed fonts (2) Default system font [1]: ").strip() or '1'
    chosen_font = 'Arial'
    chosen_font_path = None

    if src == '1' and fonts:
        print('\nInstalled fonts (first 100). Type number to select or type a substring to search:')
        for i, f in enumerate(fonts[:100], start=1):
            print(f"{i:3d}. {f}")
        sel = input("Enter number or font name (or press Enter to use first): ").strip()
        if not sel:
            chosen_font = fonts[0]
            chosen_font_path = font_map.get(chosen_font)
        else:
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(fonts):
                    chosen_font = fonts[idx]
                    chosen_font_path = font_map.get(chosen_font)
                else:
                    print("[WARN] Number out of range; trying substring match.")
            if chosen_font_path is None:
                # exact name
                if sel in font_map:
                    chosen_font = sel
                    chosen_font_path = font_map.get(sel)
                else:
                    # substring search
                    subs = [n for n in fonts if sel.lower() in n.lower()]
                    if len(subs) == 1:
                        chosen_font = subs[0]
                        chosen_font_path = font_map.get(chosen_font)
                    elif len(subs) > 1:
                        print(f"Found {len(subs)} matches, using first: {subs[0]}")
                        chosen_font = subs[0]
                        chosen_font_path = font_map.get(chosen_font)
                    else:
                        print("No match found; using typed value as font name (may fail).")
                        chosen_font = sel
                        chosen_font_path = None
    else:
        chosen_font = input("Enter default font name [Arial]: ").strip() or 'Arial'
        # try to find a file for that name via matplotlib if possible
        try:
            from matplotlib import font_manager
            for e in font_manager.fontManager.ttflist:
                if e.name.lower() == chosen_font.lower() and os.path.isfile(e.fname):
                    chosen_font_path = e.fname
                    break
        except Exception:
            pass

    font_size_input = input(f"Font size in px (default {default_font_size}): ").strip()
    try:
        font_size = int(font_size_input) if font_size_input else default_font_size
    except Exception:
        font_size = default_font_size

    font_color = input("Font color hex (e.g. #FFFFFF) [#FFFFFF]: ").strip() or "#FFFFFF"
    outline_color = input("Outline color hex (e.g. #000000) [#000000]: ").strip() or "#000000"
    position = input("Alignment (2=bottom-center, 8=top-center) [2]: ").strip() or '2'
    try:
        position = int(position)
        if position not in (2, 8):
            position = 2
    except Exception:
        position = 2

    shadow = input("Shadow size (pixels) [2]: ").strip() or '2'
    try:
        shadow = float(shadow)
    except Exception:
        shadow = 2.0

    # return both name and resolved font file path (may be None)
    return {
        'font_name': chosen_font,
        'font_path': chosen_font_path,
        'font_size': font_size,
        'font_color': font_color,
        'outline_color': outline_color,
        'position': position,
        'shadow': shadow
    }
def get_user_font_choice():
    """
    Ask user if they have a font file or want to choose from installed fonts.
    Returns: tuple (font_name_for_ass, font_file_path or None)
    """
    print("\n[FONT] Font selection")
    choice = input("Do you have a font file to use? (y/n) [n]: ").strip().lower() or 'n'

    if choice == 'y':
        path = input("Enter full path to font file (TTF/OTF): ").strip('"')
        if os.path.isfile(path):
            try:
                # Try to extract internal font name
                from fontTools.ttLib import TTFont
                tt = TTFont(path, fontNumber=0, ignoreDecompileErrors=True)
                name = None
                for record in tt['name'].names:
                    if record.nameID in (1, 4):  # 1=family, 4=full name
                        try:
                            name = record.toUnicode()
                        except Exception:
                            try:
                                name = record.string.decode('utf-8', errors='ignore')
                            except Exception:
                                name = None
                        if name:
                            break
                font_name_for_ass = name or os.path.splitext(os.path.basename(path))[0]
                print(f"[INFO] Using font file: {path} (ASS font name: {font_name_for_ass})")
                return font_name_for_ass, path
            except Exception as e:
                print(f"[WARN] Could not read font internal name ({e}), using file name")
                return os.path.splitext(os.path.basename(path))[0], path
        else:
            print("[ERROR] Font file not found, will fallback to installed fonts.")
            choice = 'n'

    # Fallback: choose from installed fonts
    try:
        from matplotlib import font_manager
        fonts = sorted({f.name: f.fname for f in font_manager.fontManager.ttflist}.items())
        if not fonts:
            print("[WARN] No installed fonts found, using Arial fallback")
            return 'Arial', None

        print("\nInstalled fonts (first 50):")
        for i, (fname, fpath) in enumerate(fonts[:50], start=1):
            print(f"{i:2d}. {fname}")
        sel = input("Enter number or font name (or press Enter to use first): ").strip()
        if not sel:
            return fonts[0][0], fonts[0][1]
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(fonts):
                return fonts[idx][0], fonts[idx][1]
            else:
                print("[WARN] Number out of range, using first")
                return fonts[0][0], fonts[0][1]
        else:
            # match substring
            matches = [f for f in fonts if sel.lower() in f[0].lower()]
            if matches:
                print(f"[INFO] Using matched font: {matches[0][0]}")
                return matches[0][0], matches[0][1]
            else:
                print("[WARN] No match found, using Arial fallback")
                return 'Arial', None
    except Exception as e:
        print(f"[WARN] Could not list installed fonts ({e}), using Arial fallback")
        return 'Arial', None


def create_and_burn(video_path, model_size='medium'):
    temp_dir = tempfile.mkdtemp(prefix='captions_')
    temp_files = []

    try:
        if not os.path.isfile(video_path):
            print('[ERROR] Video file not found:', video_path)
            return

        output_dir = os.path.dirname(video_path) or os.getcwd()
        resolution = get_video_resolution(video_path)

        json_path, transcription = transcribe_video(video_path, temp_dir, model_size=model_size)
        json_path, transcription = review_transcription(json_path, transcription)

        # ---------------- FONT CHOICE ----------------
        font_name, font_path = get_user_font_choice()

        # Caption style
        width, height = resolution
        style = {
            'font_name': font_name,
            'font_path': font_path,
            'font_size': int(max(24, height * 0.05)),
            'font_color': "#FFFFFF",
            'outline_color': "#000000",
            'position': 2,  # bottom-center
            'shadow': 2
        }
        globals()['LAST_STYLE'] = style

        # Build captions with minimal pause threshold
        # captions = build_caption_units(transcription, max_words_per_line=5, max_words_per_caption=10, pause_threshold=0.08)
        captions = build_caption_units(transcription, max_words_per_line=5, max_words_per_caption=4, pause_threshold=0.01)
        
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
        output_video = burn_subtitles_ffmpeg(video_path, ass_path, srt_path, output_dir, temp_dir)
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
    print('=== Enhanced Caption Burner ===')
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
