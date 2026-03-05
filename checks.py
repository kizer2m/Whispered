"""
Environment and dependency checks
"""
import subprocess
import sys
import importlib.metadata

from ui import info, success, warning, error, header, BRIGHT, CYAN, GREEN, YELLOW, RED, RESET


REQUIRED_PACKAGES = {
    "openai-whisper": "whisper",
    "torch": "torch",
    "tqdm": "tqdm",
    "colorama": "colorama",
}


def check_python_version():
    """Check Python version"""
    v = sys.version_info
    info(f"Python {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        error("Python 3.9 or higher is required!")
        return False
    success("Python version is compatible.")
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            success(f"FFmpeg found: {version_line[:60]}...")
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    error("FFmpeg not found! Whisper requires FFmpeg to work.")
    info("Install FFmpeg: https://ffmpeg.org/download.html")
    return False


def check_packages():
    """Check installed Python packages"""
    all_ok = True
    for pkg_name, import_name in REQUIRED_PACKAGES.items():
        try:
            version = importlib.metadata.version(pkg_name)
            success(f"{pkg_name} == {version}")
        except importlib.metadata.PackageNotFoundError:
            warning(f"{pkg_name} — not installed")
            all_ok = False
    return all_ok


def install_missing_packages():
    """Install missing packages"""
    missing = []
    for pkg_name in REQUIRED_PACKAGES:
        try:
            importlib.metadata.version(pkg_name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(pkg_name)

    if not missing:
        success("All packages are installed.")
        return True

    warning(f"Missing packages: {', '.join(missing)}")
    info("Starting installation...")

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", "requirements.txt"
        ])
        success("Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Package installation error: {e}")
        return False


def check_cuda():
    """Check CUDA (GPU) availability"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            vram = round(props.total_memory / (1024 ** 3), 1)
            cuda_ver = torch.version.cuda
            success(f"CUDA available! GPU: {BRIGHT}{gpu_name}{RESET}")
            info(f"  VRAM: {vram} GB  |  CUDA: {cuda_ver}  |  PyTorch: {torch.__version__}")
            return True
        else:
            if "cpu" in torch.__version__:
                warning("PyTorch installed without CUDA support (CPU-only version).")
                info("For GPU: pip install torch --index-url https://download.pytorch.org/whl/cu128")
            else:
                warning("CUDA not available. Transcription will use CPU only.")
            return False
    except ImportError:
        warning("PyTorch is not installed.")
        return False


def run_startup_checks() -> bool:
    """Run all startup checks"""
    header("Environment Check")
    print()

    py_ok = check_python_version()
    ff_ok = check_ffmpeg()

    print()
    header("GPU / CUDA Check")
    print()
    check_cuda()

    print()
    header("Dependency Check")
    print()
    pkg_ok = check_packages()

    if not pkg_ok:
        print()
        from ui import confirm
        if confirm("Install missing packages?"):
            pkg_ok = install_missing_packages()

    all_ok = py_ok and ff_ok and pkg_ok
    print()
    if all_ok:
        success("All checks passed!")
    else:
        if not ff_ok:
            error("Critical: FFmpeg not found.")
        if not pkg_ok:
            error("Critical: Not all packages are installed.")

    return all_ok
