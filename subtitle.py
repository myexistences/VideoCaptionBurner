# project/subtitle.py
# Enhanced with professional inner and outer glow effects
# Replicates the look of professional editing software like After Effects

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

def create_professional_glow_layers():
    """
    Professional-grade inner and outer glow effects
    Mimics After Effects / Premiere Pro style glows
    
    🎨 PROFESSIONAL GLOW CONTROL GUIDE:
    =====================================
    
    OUTER GLOW (Spreads outward from text):
    - Increase 'blur' values (15, 20, 25, 30 for massive glow)
    - Lower alpha = brighter glow
    - Multiple layers create smooth falloff
    
    INNER GLOW (Glows inside text edges):
    - Uses negative border values with blur
    - Creates rim lighting effect
    - Makes text appear luminous from within
    
    CURRENT: Professional studio-quality glow
    """
    
    layers = []
    
    # 🔥 OUTER GLOW LAYERS (Enhanced radius)
    # Layer group 1: Far outer glow (massive radius)
    layers.append({
        'blur': 20,          # 🔥 MASSIVE outer glow radius
        'border': 3,         # Thick base for spread
        'alpha': '&HD0',     # Very soft (18% opacity)
        'color': '&HFFFFFF', # White glow
        'layer': 0,
        'type': 'outer_glow'
    })
    
    # Layer group 2: Extended outer glow
    layers.append({
        'blur': 16,          # Large glow radius
        'border': 2.5,
        'alpha': '&HC0',     # Soft (25% opacity)
        'color': '&HFFFFFF',
        'layer': 1,
        'type': 'outer_glow'
    })
    
    # Layer group 3: Mid-outer glow
    layers.append({
        'blur': 12,          # Medium-large radius
        'border': 2,
        'alpha': '&HAA',     # 33% opacity
        'color': '&HFFFFFF',
        'layer': 2,
        'type': 'outer_glow'
    })
    
    # Layer group 4: Near-outer glow
    layers.append({
        'blur': 8,           # Medium radius
        'border': 1.5,
        'alpha': '&H90',     # 44% opacity
        'color': '&HFFFFFF',
        'layer': 3,
        'type': 'outer_glow'
    })
    
    # Layer group 5: Close outer glow
    layers.append({
        'blur': 5,           # Close radius
        'border': 1,
        'alpha': '&H70',     # 56% opacity
        'color': '&HFFFFFF',
        'layer': 4,
        'type': 'outer_glow'
    })
    
    # 💫 INNER GLOW LAYERS (Professional rim lighting)
    # These create the luminous effect from inside the text
    
    # Inner glow layer 1: Subtle inner rim
    layers.append({
        'blur': 2,           # Soft inner blur
        'border': -0.5,      # NEGATIVE border creates inner effect
        'alpha': '&H40',     # Bright (75% opacity)
        'color': '&HFFFFFF', # White inner glow
        'layer': 5,
        'type': 'inner_glow'
    })
    
    # Inner glow layer 2: Bright inner core
    layers.append({
        'blur': 1,           # Very soft inner blur
        'border': -1,        # NEGATIVE border pulls glow inward
        'alpha': '&H30',     # Very bright (81% opacity)
        'color': '&HFFFFFF', # White inner glow
        'layer': 6,
        'type': 'inner_glow'
    })
    
    # Black outline for contrast (between inner and outer glow)
    layers.append({
        'blur': 1,           # Slight blur for softer edge
        'border': 3.5,       # Thick outline for definition
        'alpha': '&H00',     # Fully opaque
        'color': '&H000000', # Black outline
        'layer': 7,
        'type': 'outline'
    })
    
    return layers

def write_subtitles_files(captions, style, resolution, temp_dir, base_name="captions"):
    """
    Same behavior as your version but fixes:
      - prevents outline/glow from becoming a solid block during disappearance
      - ensures exit animation ALWAYS completes before the next caption begins
    DOES NOT change any timestamps. Only changes event-layer transforms and draw order.
    """
    import os
    width, height = resolution

    srt_path = os.path.join(temp_dir, f"{base_name}.srt")
    ass_path = os.path.join(temp_dir, f"{base_name}.ass")

    # small helper to make ASS color/alpha robust (ensure trailing & if needed)
    def _ass_fix(val):
        if not isinstance(val, str):
            return val
        if val.startswith("&H") and not val.endswith("&"):
            return val + "&"
        return val

    # Base style settings
    primary_color = normalize_hex_color_to_ass(style.get('font_color', '#FFFFFF'))
    outline_color = normalize_hex_color_to_ass(style.get('outline_color', '#000000'))
    font_name = style.get('font_name', 'Arial')
    font_size = int(style.get('font_size', max(24, int(height * 0.05))))
    back_color = "&H64000000"

    # Stroke and shadow options
    outline = int(style.get('outline', 2))    # Style column outline
    shadow = float(style.get('shadow', 0.5))  # used to compute soft shadow offset

    # Position handling (unchanged)
    pos_input = style.get('position', 'bottom')
    if isinstance(pos_input, str):
        pos_input = pos_input.lower()

    if isinstance(pos_input, int) and pos_input in (1,2,3,4,5,6,7,8,9):
        align = pos_input
        margin_v = 40
    else:
        if pos_input in ("bottom", "bottom-center", "lower", "lower-center"):
            align = 2
            margin_v = 40
            if pos_input == "lower-center":
                margin_v = int(height * 0.30)
        elif pos_input in ("center", "middle", "middle-center", "center-center"):
            align = 5
            margin_v = int(height * 0.45)
        elif pos_input in ("slightly-below-center", "below-center"):
            align = 5
            margin_v = int(height * 0.55)
        elif pos_input in ("top", "top-center", "upper"):
            align = 8
            margin_v = 20
        else:
            align = 2
            margin_v = 40

    # Animation tuning
    fast_ms = int(style.get('fast_ms', 30))
    entry_start_pct = int(style.get('entry_start_pct', 85))
    exit_end_scale_pct = int(style.get('exit_end_scale_pct', 105))
    accel = float(style.get('accel', 1.0))
    preempt_ms = int(style.get('preempt_ms', 40))

    # Glow layers (use your professional layer generator)
    glow_enabled = bool(style.get('glow', True))
    glow_layers = create_professional_glow_layers() if glow_enabled else []

    # Ensure layer alpha/color strings have trailing &
    for layer in glow_layers:
        if 'alpha' in layer and isinstance(layer['alpha'], str):
            layer['alpha'] = _ass_fix(layer['alpha'])
        if 'color' in layer and isinstance(layer['color'], str):
            layer['color'] = _ass_fix(layer['color'])

    # --- Write SRT (unchanged) ---
    with open(srt_path, "w", encoding="utf-8") as srt:
        for i, c in enumerate(captions, start=1):
            srt.write(f"{i}\n")
            srt.write(f"{format_time_srt(c['start'])} --> {format_time_srt(c['end'])}\n")
            srt.write(c['text_srt'] + "\n\n")

    # --- Write ASS ---
    with open(ass_path, "w", encoding="utf-8") as ass:
        ass.write("[Script Info]\nScriptType: v4.00+\n")
        ass.write(f"PlayResX: {width}\nPlayResY: {height}\nScaledBorderAndShadow: yes\n\n")

        ass.write("[V4+ Styles]\n")
        ass.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

        # Create styles for glow layers (keeps outline column as absolute border; blur will be per-event)
        if glow_enabled:
            for i, layer in enumerate(glow_layers):
                style_name = f"GlowLayer{i}"
                border_val = abs(layer.get('border', 0))
                ass.write(f"Style: {style_name},{font_name},{font_size},{layer.get('color','&HFFFFFF')},{layer.get('color','&HFFFFFF')},{layer.get('color','&HFFFFFF')},{back_color},0,0,0,0,100,100,0,0,1,{border_val},0,{align},0,0,{margin_v},0\n")

        # Default/main style (unchanged)
        ass.write(f"Style: Default,{font_name},{font_size},{primary_color},{primary_color},{outline_color},{back_color},0,0,0,0,100,100,0,0,1,{outline},{shadow},{align},0,0,{margin_v},0\n\n")

        ass.write("[Events]\n")
        ass.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        # Draw order control:
        # - glow layers start at base_draw_layer (0..N-1)
        # - soft shadow at shadow_layer_index
        # - main text on top at main_layer_index
        base_draw_layer = 0
        glow_count = len(glow_layers)
        shadow_layer_index = base_draw_layer + glow_count
        main_layer_index = shadow_layer_index + 1

        # Iterate captions and write events
        for idx, c in enumerate(captions):
            start_time = format_time_ass(c['start'])
            end_time = format_time_ass(c['end'])
            text = c['text_ass']

            duration_ms = max(1, int((c['end'] - c['start']) * 1000))
            use_fast_ms = min(fast_ms, max(1, duration_ms // 2))

            # default exit window (finishes preempt_ms before line end)
            exit_end_rel = max(0, duration_ms - preempt_ms)
            exit_start_rel = max(0, exit_end_rel - use_fast_ms)

            # entry window
            entry_start_rel = 0
            entry_end_rel = min(use_fast_ms, max(1, duration_ms - use_fast_ms - preempt_ms))
            if entry_end_rel < 1:
                entry_end_rel = min(use_fast_ms, duration_ms // 3)
                exit_end_rel = max(entry_end_rel + 1, exit_end_rel)
                exit_start_rel = max(entry_end_rel + 1, exit_end_rel - use_fast_ms)

            # --- NEW: clamp exit so it finishes before the next caption starts (very important for smoothness)
            # Compute next caption's relative start (ms from this caption's start)
            if idx + 1 < len(captions):
                next_rel = int(round((captions[idx + 1]['start'] - c['start']) * 1000))
                # safety margin (ms) to avoid equal boundaries causing visible overlap; small value
                SAFETY_MARGIN_MS = 8
                # allowed exit end must be strictly less than next_rel - SAFETY_MARGIN_MS
                allowed_exit_end = min(exit_end_rel, next_rel - SAFETY_MARGIN_MS)
                allowed_exit_end = max(0, allowed_exit_end)

                # recompute exit window around allowed_exit_end
                exit_end_rel = allowed_exit_end
                exit_start_rel = max(0, exit_end_rel - use_fast_ms)

                # ensure entry_end < exit_start (if not, shrink entry_end_rel)
                if entry_end_rel >= exit_start_rel:
                    # attempt to shrink entry_end_rel to sit before exit_start_rel
                    new_entry_end = max(1, exit_start_rel - 1)
                    # If we cannot keep 1 ms entry (extremely tight), we fallback to 1 and let exit_start_rel be at least +1
                    entry_end_rel = min(entry_end_rel, new_entry_end)
                    if entry_end_rel < 1:
                        entry_end_rel = 1
                        exit_start_rel = max(entry_end_rel + 1, exit_start_rel)
                        exit_end_rel = max(exit_start_rel + 1, exit_end_rel)

            # If there is no next caption, exit windows stay as default (finish before event end by preempt_ms)

            # Build per-layer animation tags so every layer uses its own target alpha (no static alpha overrides)
            # start: scaled small and fully transparent
            start_state = f"\\fscx{entry_start_pct}\\fscy{entry_start_pct}\\alpha&HFF&"

            # For each glow layer, we'll build a per-layer entry transform target alpha (from layer['alpha'])
            if glow_enabled and glow_layers:
                for i, layer in enumerate(glow_layers):
                    draw_layer = base_draw_layer + i
                    style_name = f"GlowLayer{i}"

                    # Layer-specific target alpha during visible time (if not provided, use a reasonable default)
                    layer_alpha_target = layer.get('alpha', None)
                    if not layer_alpha_target:
                        # use mid alpha defaults depending on type
                        if layer.get('type') == 'inner_glow':
                            layer_alpha_target = "&H20&"   # bright inner
                        elif layer.get('type') == 'outline':
                            layer_alpha_target = "&H60&"   # semi-opaque outline (safe)
                        else:
                            layer_alpha_target = "&H80&"   # soft outer default
                    else:
                        layer_alpha_target = _ass_fix(layer_alpha_target)

                    # Compose per-layer transforms (entry -> target alpha; exit -> transparent)
                    entry_t_layer = f"\\t({entry_start_rel},{entry_end_rel},{accel},\\fscx100\\fscy100\\alpha{layer_alpha_target})"
                    exit_t_layer  = f"\\t({exit_start_rel},{exit_end_rel},{accel},\\fscx{exit_end_scale_pct}\\fscy{exit_end_scale_pct}\\alpha&HFF&)"
                    # Per-layer visual overrides (blur, border, color) but NO static alpha
                    overrides = ""
                    if 'blur' in layer and layer['blur']:
                        overrides += f"\\blur{layer['blur']}"
                    # use exact border value (negative allowed)
                    overrides += f"\\bord{layer.get('border', 0)}"
                    # color override if present
                    col = layer.get('color', primary_color)
                    if col:
                        col_str = col if isinstance(col, str) and col.endswith('&') else _ass_fix(col)
                        overrides += f"\\c{col_str}\\3c{col_str}"

                    full_tags = "{" + start_state + entry_t_layer + exit_t_layer + overrides + "}"
                    ass.write(f"Dialogue: {draw_layer},{start_time},{end_time},{style_name},,0,0,0,,{full_tags}{text}\n")

                # Soft black drop shadow underneath main text but above far-out glows
                shad_px = max(1, int(round(shadow * 2)))
                # choose a reasonable blur for the shadow
                shadow_blur = max(1.0, float(glow_layers[0].get('blur', 4)) / 3.0)
                # make shadow animate with same transforms (fade in->visible at semi, fade out->transparent)
                shadow_entry_alpha = "&H80&"
                shadow_entry = f"\\t({entry_start_rel},{entry_end_rel},{accel},\\fscx100\\fscy100\\alpha{shadow_entry_alpha})"
                shadow_exit  = f"\\t({exit_start_rel},{exit_end_rel},{accel},\\fscx{exit_end_scale_pct}\\fscy{exit_end_scale_pct}\\alpha&HFF&)"
                shadow_overrides = f"\\blur{shadow_blur}\\c&H000000&\\3c&H000000&\\shad{shad_px}"
                shadow_tags = "{" + start_state + shadow_entry + shadow_exit + shadow_overrides + "}"
                ass.write(f"Dialogue: {shadow_layer_index},{start_time},{end_time},Default,,0,0,0,,{shadow_tags}{text}\n")

            # MAIN text: build transforms that animate to fully-opaque main alpha (&H00&) and then to transparent on exit
            entry_t_main = f"\\t({entry_start_rel},{entry_end_rel},{accel},\\fscx100\\fscy100\\alpha&H00&)"
            exit_t_main  = f"\\t({exit_start_rel},{exit_end_rel},{accel},\\fscx{exit_end_scale_pct}\\fscy{exit_end_scale_pct}\\alpha&HFF&)"
            main_full_tags = "{" + start_state + entry_t_main + exit_t_main + "}"
            ass.write(f"Dialogue: {main_layer_index},{start_time},{end_time},Default,,0,0,0,,{main_full_tags}{text}\n")

    print("[INFO] ASS written with stroke, shadow, and multi-layer glow (fixed draw order and exit-clamp).")
    print("[INFO] Outline thickness:", outline, "| Shadow depth:", shadow)
    return srt_path, ass_path
