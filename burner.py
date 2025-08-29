# project/burner.py
import os
import subprocess
import shutil
import shlex
from datetime import datetime

def burn_subtitles_ffmpeg(video_path, ass_path, srt_path, output_dir, temp_dir, style):
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

        fonts_dir = None
        if style and style.get('font_path') and os.path.isfile(style.get('font_path')):
            fonts_dir = os.path.join(temp_dir, 'fonts')
            os.makedirs(fonts_dir, exist_ok=True)
            try:
                shutil.copy(style.get('font_path'), fonts_dir)
                print(f"[INFO] Copied font to fontsdir: {fonts_dir}")
            except Exception as e:
                print(f"[WARN] Could not copy font file to fontsdir: {e}")

        # 1) Try SRT + fontsdir (preferred)
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

        # 2) Try ASS (system lookup)
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