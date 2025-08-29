# project/subtitle.py
# This file is for handling subtitle appearance, styles, positions, and future animations.
# Currently, it includes writing SRT/ASS and font choice.
# You can extend this for animations (e.g., by modifying ASS events for fades, moves, etc.)

import os
import re
from helpers import format_time_ass, format_time_srt, normalize_hex_color_to_ass

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("[WARN] fontTools not installed; font name extraction may be limited.")
    TTFont = None

try:
    from matplotlib import font_manager
except ImportError:
    font_manager = None

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
            if TTFont:
                try:
                    tt = TTFont(path, fontNumber=0, ignoreDecompileErrors=True)
                    name = None
                    for record in tt['name'].names:
                        if record.nameID in (1, 4):
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
                print("[WARN] fontTools not available; using file name as font name.")
                return os.path.splitext(os.path.basename(path))[0], path
        else:
            print("[ERROR] Font file not found, will fallback to installed fonts.")
            choice = 'n'

    if font_manager:
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
            matches = [f for f in fonts if sel.lower() in f[0].lower()]
            if matches:
                print(f"[INFO] Using matched font: {matches[0][0]}")
                return matches[0][0], matches[0][1]
            else:
                print("[WARN] No match found, using Arial fallback")
                return 'Arial', None
    else:
        print("[WARN] matplotlib.font_manager not available, using Arial fallback")
        return 'Arial', None

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
    shadow = float(style.get('shadow', 2))

    # Accept position as a friendly string: 'bottom', 'center', 'lower-center', 'top', 'top-center', 'bottom-center'
    pos_input = style.get('position', 'bottom').lower() if isinstance(style.get('position'), str) else style.get('position')
    # map to ASS alignment and marginV (vertical offset)
    # ASS alignment: 1 bottom-left, 2 bottom-center, 3 bottom-right,
    # 4 middle-left, 5 middle-center, 6 middle-right,
    # 7 top-left, 8 top-center, 9 top-right
    if isinstance(pos_input, int) and pos_input in (1,2,3,4,5,6,7,8,9):
        align = pos_input
        margin_v = 40
    else:
        # string mapping
        if pos_input in ("bottom", "bottom-center", "lower", "lower-center"):
            align = 2
            margin_v = 40
            if pos_input == "lower-center":
                margin_v = int(height * 0.30)  # slightly lower than center (i.e., above bottom but below center)
        elif pos_input in ("center", "middle", "middle-center", "center-center"):
            align = 5
            margin_v = int(height * 0.45)  # center-ish (marginV will move block)
        elif pos_input in ("slightly-below-center", "below-center", "lower-center"):
            align = 5
            margin_v = int(height * 0.55)
        elif pos_input in ("top", "top-center", "upper"):
            align = 8
            margin_v = 20
        else:
            # default bottom-center
            align = 2
            margin_v = 40

    # BackColour semi-transparent black
    back = "&H64000000"

    with open(ass_path, 'w', encoding='utf-8') as ass:
        ass.write("[Script Info]\n")
        ass.write("ScriptType: v4.00+\n")
        ass.write(f"PlayResX: {width}\n")
        ass.write(f"PlayResY: {height}\n\n")

        ass.write("[V4+ Styles]\n")
        ass.write("Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        ass.write(f"Style: MyStyle,{font_name},{font_size},{primary_color},{outline_color},{back},0,0,1,2,{shadow},{align},20,20,{margin_v},0\n\n")

        ass.write("[Events]\n")
        ass.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for c in captions:
            ass_text = c['text_ass']
            # Here you can add animations/effects to ass_text, e.g., add \fad(200,200) for fade in/out
            # Example: ass_text = f"{{\\fad(200,200)}}{ass_text}"
            # Extend this for more complex animations like moving text, colors, etc.
            ass.write(f"Dialogue: 0,{format_time_ass(c['start'])},{format_time_ass(c['end'])},MyStyle,,0,0,0,,{ass_text}\n")

    return srt_path, ass_path