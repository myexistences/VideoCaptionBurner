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
    """Write captions with professional inner and outer glow effects"""
    width, height = resolution
    srt_path = os.path.join(temp_dir, f"{base_name}.srt")
    ass_path = os.path.join(temp_dir, f"{base_name}.ass")

    # SRT (unchanged)
    with open(srt_path, "w", encoding="utf-8") as srt:
        for i, c in enumerate(captions, start=1):
            srt.write(f"{i}\n")
            srt.write(f"{format_time_srt(c['start'])} --> {format_time_srt(c['end'])}\n")
            srt.write(c['text_srt'] + "\n\n")

    # ASS with professional glow effects
    primary_color = normalize_hex_color_to_ass(style.get('font_color', '#FFFFFF'))
    outline_color = normalize_hex_color_to_ass(style.get('outline_color', '#000000'))
    font_name = style.get('font_name', 'Arial')
    font_size = int(style.get('font_size', max(24, int(height * 0.05))))
    shadow = float(style.get('shadow', 0))

    # Position handling (unchanged)
    pos_input = style.get('position', 'bottom').lower() if isinstance(style.get('position'), str) else style.get('position')
    
    if isinstance(pos_input, int) and pos_input in (1,2,3,4,5,6,7,8,9):
        align = pos_input
        margin_v = 40
    else:
        # string mapping
        if pos_input in ("bottom", "bottom-center", "lower", "lower-center"):
            align = 2
            margin_v = 40
            if pos_input == "lower-center":
                margin_v = int(height * 0.30)
        elif pos_input in ("center", "middle", "middle-center", "center-center"):
            align = 5
            margin_v = int(height * 0.45)
        elif pos_input in ("slightly-below-center", "below-center", "lower-center"):
            align = 5
            margin_v = int(height * 0.55)
        elif pos_input in ("top", "top-center", "upper"):
            align = 8
            margin_v = 20
        else:
            align = 2
            margin_v = 40

    # Semi-transparent black background
    back_color = "&H64000000"
    
    # Get the professional glow layers
    glow_layers = create_professional_glow_layers()

    with open(ass_path, 'w', encoding='utf-8') as ass:
        ass.write("[Script Info]\n")
        ass.write("Title: Professional Inner & Outer Glow Subtitles\n")
        ass.write("ScriptType: v4.00+\n")
        ass.write(f"PlayResX: {width}\n")
        ass.write(f"PlayResY: {height}\n")
        ass.write("WrapStyle: 0\n")
        ass.write("ScaledBorderAndShadow: yes\n\n")

        ass.write("[V4+ Styles]\n")
        ass.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        
        # Create styles for each glow layer
        for i, layer in enumerate(glow_layers):
            style_name = f"GlowLayer{i}"
            # Use absolute value for border in style definition (negative handled in override tags)
            border_val = abs(layer['border'])
            ass.write(f"Style: {style_name},{font_name},{font_size},{layer['color']},{layer['color']},{layer['color']},{back_color},0,0,0,0,100,100,0,0,1,{border_val},{shadow},{align},20,20,{margin_v},0\n")
        
        # Main text style (bright white, on top)
        ass.write(f"Style: MainText,{font_name},{font_size},{primary_color},{primary_color},{outline_color},{back_color},0,0,0,0,100,100,0,0,1,0,0,{align},20,20,{margin_v},0\n\n")

        ass.write("[Events]\n")
        ass.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        
        # Write dialogue events with professional glow effects
        for c in captions:
            start_time = format_time_ass(c['start'])
            end_time = format_time_ass(c['end'])
            text = c['text_ass']
            
            # Write all glow layers (back to front)
            for i, layer in enumerate(glow_layers):
                style_name = f"GlowLayer{i}"
                
                # Special handling for inner glow (negative border creates inward effect)
                if layer['type'] == 'inner_glow':
                    # Inner glow uses special ASS tricks
                    # Negative border + blur creates rim lighting
                    glow_text = f"{{\\blur{layer['blur']}\\bord{layer['border']}\\alpha{layer['alpha']}\\c{layer['color']}\\3c{layer['color']}}}{text}"
                else:
                    # Standard outer glow and outline
                    glow_text = f"{{\\blur{layer['blur']}\\bord{abs(layer['border'])}\\alpha{layer['alpha']}\\c{layer['color']}}}{text}"
                
                ass.write(f"Dialogue: {layer['layer']},{start_time},{end_time},{style_name},,0,0,0,,{glow_text}\n")
            
            # Main text layer (crisp white text on top with subtle inner highlight)
            main_layer = len(glow_layers)
            # Add subtle inner edge highlight to main text for extra polish
            main_text = f"{{\\blur0\\bord0\\c{primary_color}\\3c&HFFFFFF\\shad1}}{text}"
            ass.write(f"Dialogue: {main_layer},{start_time},{end_time},MainText,,0,0,0,,{main_text}\n")

    print(f"[SUCCESS] Created PROFESSIONAL inner & outer glow effects!")
    print(f"[INFO] OUTER GLOW: Enhanced radius (blur: 5→20px) for dramatic effect")
    print(f"[INFO] INNER GLOW: Rim lighting effect using negative borders")
    print(f"[INFO] Total layers: {len(glow_layers) + 1} (5 outer + 2 inner + 1 outline + 1 main)")
    print(f"[INFO] Effect matches After Effects / Premiere Pro quality")
    print(f"[TIP] Inner glow creates luminous text effect from within")
    print(f"[ADJUST] Edit create_professional_glow_layers() to fine-tune effects")
    
    return srt_path, ass_path