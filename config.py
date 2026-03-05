"""
Whispered application configuration
"""
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "source")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ─── Whisper Model ───────────────────────────────────────────────────────────
# Available models: tiny, base, small, medium, large-v1, large-v2, large-v3, turbo
DEFAULT_MODEL = "small"

# ─── Device (CPU / GPU) ─────────────────────────────────────────────────────
# "cpu" — processor, "cuda" — NVIDIA GPU
DEFAULT_DEVICE = "auto"  # "auto" will detect automatically

# ─── Supported video formats ────────────────────────────────────────────────
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".mts"
}

# ─── Language (None = auto-detect) ──────────────────────────────────────────
DEFAULT_LANGUAGE = None

# ─── Application version ────────────────────────────────────────────────────
APP_VERSION = "1.1.0"
APP_NAME = "Whispered"


# ─── Device detection utilities ─────────────────────────────────────────────
def detect_device() -> str:
    """Detect the best available device"""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def get_gpu_info() -> dict | None:
    """Get GPU information (if available)"""
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return {
                "name": torch.cuda.get_device_name(0),
                "memory_gb": round(props.total_memory / (1024 ** 3), 1),
                "cuda_version": torch.version.cuda,
                "compute_capability": f"{props.major}.{props.minor}",
            }
    except Exception:
        pass
    return None


def resolve_device(device_setting: str) -> str:
    """Resolve device setting to actual value"""
    if device_setting == "auto":
        return detect_device()
    return device_setting
