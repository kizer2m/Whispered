"""
╔══════════════════════════════════════════════════════════════════╗
║   Whispered — Console Video Transcription Application          ║
║   Powered by OpenAI Whisper speech recognition                 ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os
import sys

# Add current directory to PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    MODELS_DIR, APP_VERSION, APP_NAME,
    DEFAULT_LANGUAGE, DEFAULT_DEVICE, detect_device, get_gpu_info, resolve_device,
    get_source_dir, get_output_dir, set_source_dir, set_output_dir,
    reset_source_dir, reset_output_dir, _DEFAULT_SOURCE_DIR, _DEFAULT_OUTPUT_DIR
)
from ui import (
    banner, header, info, success, warning, error, bullet, confirm,
    clear_screen, BRIGHT, CYAN, GREEN, YELLOW, MAGENTA, RED, WHITE, RESET, DIM
)


def ensure_directories():
    """Create required directories"""
    header("Directory Check")
    dirs = {
        "source": get_source_dir(),
        "output": get_output_dir(),
        "models": MODELS_DIR,
    }
    for name, path in dirs.items():
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            success(f"Created folder: {name}/")
        else:
            success(f"Folder found: {name}/")


def show_main_menu(model_loaded: bool, current_model: str | None,
                   language: str | None, device: str):
    """Render the main menu"""
    print()

    # Model status
    if model_loaded:
        model_status = f"{GREEN}● Model: {BRIGHT}{current_model}{RESET}"
    else:
        model_status = f"{RED}○ No model loaded{RESET}"

    # Language status
    lang_display = language if language else "auto"
    lang_status = f"{CYAN}Lang: {lang_display}{RESET}"

    # Device status
    if device == "cuda":
        gpu_info = get_gpu_info()
        gpu_name = gpu_info["name"] if gpu_info else "GPU"
        device_status = f"{GREEN}⚡ GPU: {gpu_name}{RESET}"
    else:
        device_status = f"{YELLOW}💻 CPU{RESET}"

    print(f"  {model_status}    {lang_status}    {device_status}")
    print()

    print(f"  {BRIGHT}{CYAN}{'═' * 50}{RESET}")
    print(f"  {BRIGHT}{WHITE}  MAIN MENU{RESET}")
    print(f"  {BRIGHT}{CYAN}{'═' * 50}{RESET}")
    print()

    items = [
        ("1", "📋  File Status",               "View video files and processing status"),
        ("2", "🚀  Transcribe All",             "Process all pending files"),
        ("3", "🎯  Select Files",               "Transcribe selected files"),
        ("4", "🔄  Re-transcribe",              "Overwrite result for a file"),
        ("5", "🧠  Model Management",           "Download / switch Whisper model"),
        ("6", "🌐  Change Language",            "Set language or auto-detect"),
        ("7", "⚡  Switch CPU / GPU",            f"Current device: {'GPU (CUDA)' if device == 'cuda' else 'CPU'}"),
        ("8", "🔍  Environment Check",          "Re-check dependencies"),
        ("9", "📂  Open Folders",               "Open source / output in file explorer"),
        ("0", "🚪  Exit",                       ""),
    ]

    for key, title, desc in items:
        if desc:
            print(f"  {BRIGHT}{CYAN}[{key}]{RESET}  {title}")
            print(f"       {DIM}{desc}{RESET}")
        else:
            print(f"  {BRIGHT}{CYAN}[{key}]{RESET}  {title}")
        print()


def select_device(current_device: str) -> str:
    """CPU / GPU switching menu"""
    header("Select Transcription Device")

    gpu_info = get_gpu_info()
    cuda_available = gpu_info is not None

    print()
    current_label = "GPU (CUDA)" if current_device == "cuda" else "CPU"
    info(f"Current device: {BRIGHT}{current_label}{RESET}")
    print()

    # CPU option
    cpu_marker = f"  {GREEN}← current{RESET}" if current_device == "cpu" else ""
    print(f"  {BRIGHT}{CYAN}[1]{RESET}  💻  CPU (Central Processing Unit){cpu_marker}")
    print(f"       {DIM}Slower, but always available. Works with any model.{RESET}")
    print()

    # GPU option
    if cuda_available:
        gpu_marker = f"  {GREEN}← current{RESET}" if current_device == "cuda" else ""
        vram = gpu_info["memory_gb"]
        print(f"  {BRIGHT}{CYAN}[2]{RESET}  ⚡  GPU — {BRIGHT}{gpu_info['name']}{RESET} ({vram} GB VRAM){gpu_marker}")
        print(f"       {DIM}5-10x faster than CPU. CUDA {gpu_info['cuda_version']}. Recommended!{RESET}")

        # VRAM warnings for large models
        if vram < 4:
            print(f"       {YELLOW}⚠ Low VRAM — recommended models: tiny, base, small{RESET}")
        elif vram < 8:
            print(f"       {DIM}Recommended models: up to medium{RESET}")
    else:
        print(f"  {RED}[2]{RESET}  ⚡  GPU — {RED}Not available{RESET}")
        print(f"       {DIM}CUDA not detected. Make sure PyTorch with CUDA is installed.{RESET}")

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back\n")

    choice = input("  Select device: ").strip()

    if choice == "1":
        success("Device: CPU")
        return "cpu"
    elif choice == "2" and cuda_available:
        success(f"Device: GPU ({gpu_info['name']})")
        return "cuda"
    elif choice == "2" and not cuda_available:
        error("GPU not available!")
        return current_device
    else:
        info("Device unchanged.")
        return current_device


def select_language(current: str | None) -> str | None:
    """Language selection menu"""
    header("Transcription Language")

    languages = [
        ("auto",  "Auto-detect (recommended)"),
        ("en",    "English"),
        ("ru",    "Russian"),
        ("uk",    "Ukrainian"),
        ("de",    "German"),
        ("fr",    "French"),
        ("es",    "Spanish"),
        ("it",    "Italian"),
        ("ja",    "Japanese"),
        ("zh",    "Chinese"),
        ("ko",    "Korean"),
        ("pt",    "Portuguese"),
        ("ar",    "Arabic"),
        ("hi",    "Hindi"),
        ("tr",    "Turkish"),
        ("pl",    "Polish"),
    ]

    current_display = current if current else "auto"
    info(f"Current language: {BRIGHT}{current_display}{RESET}")
    print()

    for i, (code, name) in enumerate(languages):
        marker = f"  {GREEN}← current{RESET}" if (code == current or (code == "auto" and current is None)) else ""
        bullet(f"{name} ({code}){marker}", i)

    print()
    try:
        choice = int(input("  Select option: ").strip())
        if 0 <= choice < len(languages):
            code = languages[choice][0]
            selected = None if code == "auto" else code
            selected_display = languages[choice][1]
            success(f"Language set: {selected_display}")
            return selected
    except (ValueError, IndexError):
        pass
    warning("Language unchanged.")
    return current


def open_folders():
    """Open folders and set custom paths"""
    header("Folders")

    src = get_source_dir()
    out = get_output_dir()
    src_custom = src != _DEFAULT_SOURCE_DIR
    out_custom = out != _DEFAULT_OUTPUT_DIR

    print()
    info(f"Source: {BRIGHT}{src}{RESET}" + (f"  {YELLOW}(custom){RESET}" if src_custom else ""))
    info(f"Output: {BRIGHT}{out}{RESET}" + (f"  {YELLOW}(custom){RESET}" if out_custom else ""))
    print()

    bullet("Open source folder in explorer", 1)
    bullet("Open output folder in explorer", 2)
    bullet("Open both folders", 3)
    print()
    bullet(f"Set custom source folder", 4)
    bullet(f"Set custom output folder", 5)
    if src_custom or out_custom:
        bullet(f"Reset to default folders", 6)
    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back\n")

    choice = input("  Select: ").strip()

    if choice == "1":
        if os.path.exists(src):
            os.startfile(src)
        else:
            error(f"Folder does not exist: {src}")
    elif choice == "2":
        if os.path.exists(out):
            os.startfile(out)
        else:
            error(f"Folder does not exist: {out}")
    elif choice == "3":
        for d in (src, out):
            if os.path.exists(d):
                os.startfile(d)
    elif choice == "4":
        _set_custom_folder("source")
    elif choice == "5":
        _set_custom_folder("output")
    elif choice == "6" and (src_custom or out_custom):
        reset_source_dir()
        reset_output_dir()
        success(f"Reset to defaults:")
        info(f"  Source: {get_source_dir()}")
        info(f"  Output: {get_output_dir()}")


def _set_custom_folder(folder_type: str):
    """Set a custom source or output folder path"""
    current = get_source_dir() if folder_type == "source" else get_output_dir()
    header(f"Set Custom {folder_type.capitalize()} Folder")
    print()
    info(f"Current: {BRIGHT}{current}{RESET}")
    info("Enter the full path to the folder, or leave empty to cancel.")
    print()

    path = input("  Path: ").strip().strip('"').strip("'")

    if not path:
        info("Cancelled.")
        return

    path = os.path.abspath(path)

    if not os.path.exists(path):
        warning(f"Folder does not exist: {path}")
        if confirm("Create it?"):
            try:
                os.makedirs(path, exist_ok=True)
                success(f"Created: {path}")
            except Exception as e:
                error(f"Failed to create folder: {e}")
                return
        else:
            return

    if not os.path.isdir(path):
        error("The specified path is not a directory.")
        return

    if folder_type == "source":
        set_source_dir(path)
    else:
        set_output_dir(path)

    success(f"{folder_type.capitalize()} folder set to: {BRIGHT}{path}{RESET}")


def main():
    """Main application function"""
    clear_screen()
    banner(APP_NAME, APP_VERSION)

    # 1. Create directories
    ensure_directories()

    # 2. Environment check
    from checks import run_startup_checks
    if not run_startup_checks():
        if not confirm("Continue despite errors?"):
            sys.exit(1)

    # 3. Device detection (auto: GPU if available, else CPU)
    device = resolve_device(DEFAULT_DEVICE)
    gpu_info = get_gpu_info()
    header("Transcription Device")
    if device == "cuda" and gpu_info:
        success(f"⚡ GPU: {gpu_info['name']} ({gpu_info['memory_gb']} GB VRAM)")
        info("Model will be loaded on GPU for maximum speed.")
    else:
        info("💻 Using CPU. Switch to GPU for faster processing (option 7).")

    # 4. Model check
    from model_manager import check_model_on_startup, load_model, show_models_menu, select_and_download_model

    current_model_name = check_model_on_startup()
    model = None
    model_loaded = False

    if current_model_name:
        try:
            model = load_model(current_model_name, device=device)
            model_loaded = True
        except Exception as e:
            error(f"Failed to load model on {device}: {e}")
            if device == "cuda":
                warning("Falling back to CPU...")
                try:
                    device = "cpu"
                    model = load_model(current_model_name, device="cpu")
                    model_loaded = True
                except Exception as e2:
                    error(f"Failed to load model: {e2}")

    language = DEFAULT_LANGUAGE

    # 5. Main menu loop
    from transcriber import (
        show_files_status, transcribe_all, transcribe_selected, retranscribe_file
    )

    while True:
        show_main_menu(model_loaded, current_model_name, language, device)
        choice = input(f"  {BRIGHT}Your choice:{RESET} ").strip()

        if choice == "1":
            show_files_status()

        elif choice == "2":
            if not model_loaded:
                error("Load a model first! (option 5)")
                continue
            transcribe_all(model, language)

        elif choice == "3":
            if not model_loaded:
                error("Load a model first! (option 5)")
                continue
            transcribe_selected(model, language)

        elif choice == "4":
            if not model_loaded:
                error("Load a model first! (option 5)")
                continue
            retranscribe_file(model, language)

        elif choice == "5":
            result = show_models_menu()
            if result:
                try:
                    current_model_name = result
                    model = load_model(current_model_name, device=device)
                    model_loaded = True
                except Exception as e:
                    error(f"Failed to load model: {e}")

        elif choice == "6":
            language = select_language(language)

        elif choice == "7":
            new_device = select_device(device)
            if new_device != device:
                device = new_device
                # Reload model on new device
                if model_loaded and current_model_name:
                    info("Reloading model on new device...")
                    try:
                        model = load_model(current_model_name, device=device)
                        model_loaded = True
                        success("Model reloaded!")
                    except Exception as e:
                        error(f"Error: {e}")
                        if device == "cuda":
                            warning("Falling back to CPU...")
                            device = "cpu"
                            try:
                                model = load_model(current_model_name, device="cpu")
                            except Exception:
                                model_loaded = False

        elif choice == "8":
            run_startup_checks()

        elif choice == "9":
            open_folders()

        elif choice == "0":
            print()
            success("Goodbye! 🎙")
            print()
            sys.exit(0)

        else:
            warning("Invalid choice. Try again.")

        if choice != "0":
            print()
            input(f"  {DIM}Press Enter to continue...{RESET}")
            clear_screen()
            banner(APP_NAME, APP_VERSION)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Interrupted by user (Ctrl+C){RESET}\n")
        sys.exit(0)
