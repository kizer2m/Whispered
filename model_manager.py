"""
Whisper model manager — download, check, select models
"""
import os
import whisper
from config import MODELS_DIR, DEFAULT_MODEL
from ui import info, success, warning, error, bullet, confirm, header, format_size, BRIGHT, CYAN, RESET, GREEN, YELLOW


# ─── Model size information (approximate) ───────────────────────────────────
MODEL_INFO = {
    "tiny":        {"size": "~75 MB",    "params": "39M",    "speed": "★★★★★",  "quality": "★★☆☆☆"},
    "tiny.en":     {"size": "~75 MB",    "params": "39M",    "speed": "★★★★★",  "quality": "★★☆☆☆"},
    "base":        {"size": "~145 MB",   "params": "74M",    "speed": "★★★★☆",  "quality": "★★★☆☆"},
    "base.en":     {"size": "~145 MB",   "params": "74M",    "speed": "★★★★☆",  "quality": "★★★☆☆"},
    "small":       {"size": "~465 MB",   "params": "244M",   "speed": "★★★☆☆",  "quality": "★★★★☆"},
    "small.en":    {"size": "~465 MB",   "params": "244M",   "speed": "★★★☆☆",  "quality": "★★★★☆"},
    "medium":      {"size": "~1.5 GB",   "params": "769M",   "speed": "★★☆☆☆",  "quality": "★★★★☆"},
    "medium.en":   {"size": "~1.5 GB",   "params": "769M",   "speed": "★★☆☆☆",  "quality": "★★★★☆"},
    "large-v1":    {"size": "~2.9 GB",   "params": "1550M",  "speed": "★☆☆☆☆",  "quality": "★★★★★"},
    "large-v2":    {"size": "~2.9 GB",   "params": "1550M",  "speed": "★☆☆☆☆",  "quality": "★★★★★"},
    "large-v3":    {"size": "~2.9 GB",   "params": "1550M",  "speed": "★☆☆☆☆",  "quality": "★★★★★"},
    "turbo":       {"size": "~1.5 GB",   "params": "809M",   "speed": "★★★☆☆",  "quality": "★★★★★"},
}


def get_available_models() -> list[str]:
    """Get list of all available Whisper models"""
    return whisper.available_models()


def get_downloaded_models() -> list[str]:
    """Get list of already downloaded models"""
    if not os.path.exists(MODELS_DIR):
        return []
    downloaded = []
    for f in os.listdir(MODELS_DIR):
        if f.endswith(".pt"):
            name = f.replace(".pt", "")
            downloaded.append(name)
    return downloaded


def is_model_downloaded(model_name: str) -> bool:
    """Check if a specific model is downloaded"""
    model_path = os.path.join(MODELS_DIR, f"{model_name}.pt")
    return os.path.exists(model_path)


def download_model(model_name: str) -> bool:
    """Download a Whisper model to the models folder"""
    try:
        info(f"Downloading model '{model_name}' — this may take a while...")
        # Download on CPU to avoid occupying GPU memory
        whisper.load_model(model_name, download_root=MODELS_DIR, device="cpu")
        success(f"Model '{model_name}' downloaded successfully!")
        return True
    except Exception as e:
        error(f"Model download error: {e}")
        return False


def load_model(model_name: str, device: str = "cpu"):
    """Load model from local folder onto the specified device"""
    device_label = "GPU (CUDA)" if device == "cuda" else "CPU"
    info(f"Loading model '{model_name}' into memory on {device_label}...")
    model = whisper.load_model(model_name, download_root=MODELS_DIR, device=device)
    success(f"Model '{model_name}' ready on {device_label}.")
    return model


def check_model_on_startup() -> str | None:
    """
    Check model on startup.
    Returns available model name or None.
    """
    header("Whisper Models Check")

    downloaded = get_downloaded_models()
    if downloaded:
        success(f"Models found: {len(downloaded)}")
        for m in downloaded:
            mi = MODEL_INFO.get(m, {})
            size = mi.get("size", "?")
            bullet(f"{BRIGHT}{m}{RESET}  ({size})")
        return downloaded[0] if DEFAULT_MODEL not in downloaded else DEFAULT_MODEL
    else:
        warning("No Whisper models found in models/ folder.")
        info("At least one model is required for transcription.")
        if confirm("Download a model now?"):
            return select_and_download_model()
        return None


def select_and_download_model() -> str | None:
    """Interactive model selection and download"""
    print()
    header("Select Model to Download")
    print()

    recommended = ["tiny", "base", "small", "medium", "turbo", "large-v3"]
    for i, name in enumerate(recommended, 1):
        mi = MODEL_INFO.get(name, {})
        size = mi.get("size", "?")
        speed = mi.get("speed", "?")
        quality = mi.get("quality", "?")
        downloaded = "✔ downloaded" if is_model_downloaded(name) else ""
        marker = f"  {GREEN}{downloaded}{RESET}" if downloaded else ""
        print(f"  {BRIGHT}{CYAN}[{i}]{RESET}  {BRIGHT}{name:<12}{RESET}  "
              f"Size: {YELLOW}{size:<10}{RESET}  "
              f"Speed: {speed}  Quality: {quality}{marker}")

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back")
    print()

    while True:
        try:
            choice = input(f"  Select model (1-{len(recommended)}, 0 — back): ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(recommended):
                model_name = recommended[idx]
                if is_model_downloaded(model_name):
                    info(f"Model '{model_name}' is already downloaded.")
                    return model_name
                print()
                if download_model(model_name):
                    return model_name
                return None
        except (ValueError, IndexError):
            error("Invalid input. Try again.")


def show_models_menu():
    """Model management menu"""
    header("Model Management")

    downloaded = get_downloaded_models()
    all_models = get_available_models()

    print(f"\n  Downloaded: {BRIGHT}{GREEN}{len(downloaded)}{RESET} of {len(all_models)} available\n")

    for m in all_models:
        mi = MODEL_INFO.get(m, {})
        size = mi.get("size", "?")
        status = f"{GREEN}● downloaded{RESET}" if m in downloaded else f"{YELLOW}○ not downloaded{RESET}"
        print(f"    {BRIGHT}{m:<16}{RESET}  {size:<12}  {status}")

    print()
    if confirm("Download an additional model?"):
        return select_and_download_model()
    return None
