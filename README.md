
# 🎥 VideoCaptionBurner

[![GitHub Views](https://komarev.com/ghpvc/?username=myexistences&repo=VideoCaptionBurner&color=blueviolet&style=flat&label=Views)](https://github.com/myexistences/VideoCaptionBurner)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/myexistences/VideoCaptionBurner?style=social)](https://github.com/myexistences/VideoCaptionBurner/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/myexistences/VideoCaptionBurner?style=social)](https://github.com/myexistences/VideoCaptionBurner/network/members)

**Elevate your videos with AI-powered, studio-grade captions.**  
VideoCaptionBurner is your ultimate tool for transforming raw videos into polished masterpieces. Powered by OpenAI's Whisper for lightning-fast transcription, it generates customizable subtitles with pro-level effects like multi-layer glows, shadows, and animations. Burn them seamlessly into your video using FFmpeg – all in one sleek, user-friendly package. Perfect for creators, editors, and storytellers who demand perfection. 🚀

# ![Demo Video](https://github.com/gamingnove6/Demo/raw/refs/heads/main/Demo-1.mp4)  
▶ [Watch the Demo Video on Vimeo](https://vimeo.com/1114347947)




## ✨ Key Features
- **AI Transcription Magic**: Whisper model delivers word-level accuracy with editable reviews. No more manual timing headaches.
- **Smart Caption Logic**: Custom pause thresholds group words naturally – continue lines or vanish captions during long gaps.
- **Hollywood-Style Effects**: Inner/outer glows, crisp outlines, dynamic shadows, and subtle animations for that premium vibe.
- **Font Freedom**: Pick from system fonts or drop in your custom TTF/OTF – total control.
- **Dual Subtitle Output**: SRT for simplicity, ASS for advanced styling.
- **Effortless Burning**: FFmpeg integration with smart fallbacks ensures flawless video output.
- **Cross-Platform Cool**: Windows batch launcher included; runs smooth on macOS/Linux too.

## 🛠 Requirements
- **Python 3.12+**: The brain behind the operation.
- **FFmpeg (Full Build)**: Essential for video magic. Grab it from [ffmpeg.org](https://ffmpeg.org/download.html) – add to PATH for seamless integration.
- **Python Packages**: Auto-handled via `requirements.txt` (Whisper, FontTools, etc.).

## 🚀 Installation
1. Clone the repo:  
   ```bash
   git clone https://github.com/myexistences/VideoCaptionBurner.git
   cd VideoCaptionBurner
   ```

2. Install deps:  
   ```bash
   pip install -r requirements.txt
   ```
   *(Pro Tip: If Whisper acts up, check PyTorch compatibility in their docs.)*

3. Set up FFmpeg:  
   - **Windows**: Download full build (gyan.dev recommended). Extract, add `bin` to PATH.  
   - **macOS**: `brew install ffmpeg`.  
   - **Linux**: `sudo apt install ffmpeg` (or equivalent).  
   Verify: `ffmpeg -version`.

## 📖 How to Use
Fire it up and let the tool guide you – it's interactive and foolproof!

### Windows Quick Launch
- Double-click `Run.bat`. It checks everything, installs missing deps, and starts the show.

### Manual Mode (Any OS)
```bash
python main.py
```

**Step-by-Step Flow**:
1. **Input Video**: Drop the full path to your MP4 (e.g., `/path/to/video.mp4`).
2. **Whisper Model**: Pick size – `medium` for speed + accuracy balance.
3. **Tune Pauses**: Set gaps (ms) for line continuation or caption breaks.
4. **Style It Up**: Choose font, size, colors, position (bottom/center/top), shadow depth.
5. **Review & Edit**: Tweak transcription segments on the fly.
6. **Output**: Get a fresh `captioned_YYYYMMDD_HHMMSS.mp4` in the same folder. Temp files? Auto-cleaned. 😎

**Pro Tip**: For epic results, experiment with glow layers in `subtitle.py` – it's like After Effects in code!

## 🗂 Project Structure
Keepin' it simple and modular – no bloat here:

```
VideoCaptionBurner/
├── main.py                # The boss: Orchestrates everything.
├── transcription.py       # AI transcription + review mode.
├── caption_builder.py     # Smart caption grouping logic.
├── subtitle.py            # Font picker + pro styling (glows, shadows).
├── burner.py              # FFmpeg burner with fallbacks.
├── helpers.py             # Utils: Time formats, colors, resolution.
├── Run.bat                # Windows launcher – checks & runs.
├── requirements.txt       # All the deps in one spot.
└── README.md              # You're reading it. 🔥
```

## 🔗 Dependencies
- `openai-whisper`: Transcription powerhouse.
- `fonttools` & `matplotlib`: Font handling pros.
- FFmpeg: The video wizard (external, not pip-installable).

## 🤝 Contributing
Love it? Fork, tweak, PR! Issues welcome for bugs or wild ideas.  
- Stick to PEP 8.
- Test cross-platform.
- Star the repo if it rocks your world! ⭐

## 📄 License
MIT – Free to use, modify, and share. See [LICENSE](LICENSE) for deets.

---

Crafted by [@myexistences](https://github.com/myexistences). Drop a star, fork, or watch – let's make videos epic together! 🌟
```
