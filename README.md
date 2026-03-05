# 🎙 Whispered — Video Transcription Tool

A console application for automatic video transcription powered by **OpenAI Whisper**.  
Supports **GPU (CUDA)** and **CPU** modes.

---

## 📋 Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Python** | 3.9+ | Tested with 3.11 |
| **FFmpeg** | Any recent | Must be in system PATH |
| **NVIDIA GPU** | Optional | CUDA-compatible GPU for acceleration |

---

## 🚀 Installation

### 1. Clone or download the project

Place the project files into a folder, for example `E:\Whispered\`.

### 2. Install Python dependencies

```bash
cd E:\Whispered
pip install -r requirements.txt
```

### 3. Install PyTorch with GPU support (recommended)

By default, `pip install torch` installs the **CPU-only** version.  
To use your NVIDIA GPU, install PyTorch with CUDA:

```bash
# First, remove the CPU-only version
pip uninstall torch torchvision torchaudio -y

# Then install with CUDA 12.8 support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

> **Note:** Check your NVIDIA driver version with `nvidia-smi`. The CUDA version shown there must be ≥ the CUDA version in the PyTorch package (12.8).

### 4. Install FFmpeg

Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to your system PATH.

Verify it works:
```bash
ffmpeg -version
```

---

## ▶️ Running the Application

### Option 1: Double-click the batch file

```
E:\Whispered\start.bat
```

### Option 2: Run from the command line

```bash
python E:\Whispered\whispered.py
```

On first launch, the program will:
1. **Create directories** — `source/`, `output/`, `models/` are created automatically
2. **Check environment** — Python version, FFmpeg, CUDA/GPU, all pip packages
3. **Check models** — if no model is found, offers interactive download
4. **Auto-detect GPU** — uses GPU by default if CUDA is available

---

## 📁 Project Structure

```
Whispered/
├── whispered.py        # Main entry point and menu
├── config.py           # Configuration + GPU/CPU detection
├── ui.py               # Console output utilities
├── model_manager.py    # Whisper model management
├── transcriber.py      # Transcription engine (GPU fp16 / CPU fp32)
├── checks.py           # Environment & CUDA checks
├── requirements.txt    # Python dependencies
├── start.bat           # Windows launcher
├── source/             # 📥 Input: video files to transcribe
├── output/             # 📤 Output: transcription text files
└── models/             # 🧠 Whisper model files (.pt)
```

---

## 🖥 Menu Overview

```
  ● Model: small    Lang: auto    ⚡ GPU: NVIDIA GeForce RTX 3050

  ══════════════════════════════════════════════════
    MAIN MENU
  ══════════════════════════════════════════════════

  [1]  📋  File Status           — View video files and processing status
  [2]  🚀  Transcribe All        — Process all pending files
  [3]  🎯  Select Files          — Transcribe selected files
  [4]  🔄  Re-transcribe         — Overwrite result for a file
  [5]  🧠  Model Management      — Download / switch Whisper model
  [6]  🌐  Change Language       — Set language or auto-detect
  [7]  ⚡  Switch CPU / GPU      — Toggle between CPU and GPU
  [8]  🔍  Environment Check     — Re-check dependencies
  [9]  📂  Open Folders          — Open source / output in file explorer
  [0]  🚪  Exit
```

---

## 🧠 Available Models

| Model | Size | Speed | Quality | GPU VRAM |
|-------|------|-------|---------|----------|
| `tiny` | ~75 MB | ★★★★★ | ★★☆☆☆ | ~1 GB |
| `base` | ~145 MB | ★★★★☆ | ★★★☆☆ | ~1 GB |
| `small` | ~465 MB | ★★★☆☆ | ★★★★☆ | ~2 GB |
| `medium` | ~1.5 GB | ★★☆☆☆ | ★★★★☆ | ~5 GB |
| `turbo` | ~1.5 GB | ★★★☆☆ | ★★★★★ | ~6 GB |
| `large-v3` | ~2.9 GB | ★☆☆☆☆ | ★★★★★ | ~10 GB |

> **Tip:** For a 6 GB VRAM GPU (e.g. RTX 3050), models up to `medium` work comfortably. Use `turbo` with caution. For `large-v3`, switch to CPU.

---

## ⚡ CPU vs GPU

| Feature | CPU | GPU (CUDA) |
|---------|-----|------------|
| Speed | Baseline | 5-10x faster |
| Precision | fp32 | fp16 (half precision) |
| Availability | Always | Requires NVIDIA GPU |
| VRAM | Uses RAM | Limited by GPU memory |
| Switching | Menu option [7] | Menu option [7] |

The model is **automatically reloaded** when switching between CPU and GPU.  
If GPU runs out of memory, the program **falls back to CPU** automatically.

---

## 📄 Output Format

For each video file (e.g. `interview.mp4`), a text file is created (`interview.txt`):

```
# Transcription: interview.mp4
# Language: en
# Processing time: 2m 34s
# ============================================================

Full transcription text goes here...

# ============================================================
# Segmented transcription with timestamps:
# ============================================================

[00:00:00.000 --> 00:00:03.520]  Hello and welcome to the show.
[00:00:03.520 --> 00:00:07.840]  Today we're going to talk about...
```

---

## 🎬 Supported Video Formats

`.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm` `.m4v` `.mpg` `.mpeg` `.3gp` `.ts` `.mts`

---

## 🌐 Supported Languages

Auto-detection is recommended. Manual selection available for:

English, Russian, Ukrainian, German, French, Spanish, Italian, Japanese, Chinese, Korean, Portuguese, Arabic, Hindi, Turkish, Polish — and [90+ more languages](https://github.com/openai/whisper#available-models-and-languages) supported by Whisper.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `CUDA not available` | Install PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| `FFmpeg not found` | Install FFmpeg and add to PATH |
| `Out of memory` on GPU | Switch to a smaller model or use CPU (option 7) |
| Slow transcription | Switch to GPU (option 7) or use a smaller model |
| Wrong language detected | Set language manually (option 6) |
