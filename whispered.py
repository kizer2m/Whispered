"""
╔══════════════════════════════════════════════════════════════════╗
║   Whispered — Console Video & Audio Transcription App           ║
║   Powered by OpenAI Whisper speech recognition                  ║
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
    reset_source_dir, reset_output_dir, _DEFAULT_SOURCE_DIR, _DEFAULT_OUTPUT_DIR,
    load_settings, save_settings,
)
from ui import (
    banner, header, info, success, warning, error, bullet, confirm,
    clear_screen, BRIGHT, CYAN, GREEN, YELLOW, MAGENTA, RED, WHITE, RESET, DIM,
)


# ─── State helper ─────────────────────────────────────────────────────────────

def _state_to_settings(state: dict) -> dict:
    """Convert runtime state to the settings schema for persistence."""
    src = get_source_dir()
    out = get_output_dir()
    return {
        "model":      state.get("model_name"),
        "device":     state.get("device", DEFAULT_DEVICE),
        "language":   state.get("language"),
        "translate":  state.get("translate", False),
        "recursive":  state.get("recursive", False),
        "export_txt": state.get("export_txt", True),
        "export_srt": state.get("export_srt", True),
        "export_vtt": state.get("export_vtt", True),
        "source_dir": src if src != _DEFAULT_SOURCE_DIR else None,
        "output_dir": out if out != _DEFAULT_OUTPUT_DIR else None,
    }


# ─── Startup ──────────────────────────────────────────────────────────────────

def ensure_directories():
    """Create required directories."""
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


# ─── Menu rendering ───────────────────────────────────────────────────────────

def _bool_label(v: bool) -> str:
    return f"{GREEN}ON{RESET}" if v else f"{RED}OFF{RESET}"


def show_main_menu(state: dict):
    """Render the main menu using state dict."""
    model_name  = state.get("model_name")
    model_loaded = state.get("model_loaded", False)
    language    = state.get("language")
    device      = state.get("device", "cpu")
    translate   = state.get("translate", False)
    recursive   = state.get("recursive", False)
    export_txt  = state.get("export_txt", True)
    export_srt  = state.get("export_srt", True)
    export_vtt  = state.get("export_vtt", True)

    print()

    # Status bar
    if model_loaded:
        model_status = f"{GREEN}● {BRIGHT}{model_name}{RESET}"
    else:
        model_status = f"{RED}○ No model{RESET}"

    lang_display  = language if language else "auto"
    lang_status   = f"{CYAN}Lang: {lang_display}{RESET}"

    if device == "cuda":
        gpu_info = get_gpu_info()
        gpu_name = gpu_info["name"] if gpu_info else "GPU"
        device_status = f"{GREEN}⚡ {gpu_name}{RESET}"
    else:
        device_status = f"{YELLOW}💻 CPU{RESET}"

    mode_parts = []
    if translate:
        mode_parts.append(f"{YELLOW}↩ Translate→EN{RESET}")
    if recursive:
        mode_parts.append(f"{CYAN}↻ Recursive{RESET}")
    fmts = []
    for name, flag in [("txt", export_txt), ("srt", export_srt), ("vtt", export_vtt)]:
        if flag: fmts.append(name)
    if fmts:
        mode_parts.append(f"{DIM}[{' '.join(fmts)}]{RESET}")

    mode_str = "  ".join(mode_parts) if mode_parts else ""

    print(f"  {model_status}    {lang_status}    {device_status}")
    if mode_str:
        print(f"  {mode_str}")
    print()

    print(f"  {BRIGHT}{CYAN}{'═' * 52}{RESET}")
    print(f"  {BRIGHT}{WHITE}  MAIN MENU{RESET}")
    print(f"  {BRIGHT}{CYAN}{'═' * 52}{RESET}")
    print()

    items = [
        ("1",  "📋  File Status",
               f"View files in source folder{' (recursive)' if recursive else ''}"),
        ("2",  "🚀  Transcribe All",
               "Process all pending files"),
        ("3",  "🎯  Select Files",
               "Transcribe selected files"),
        ("4",  "🔄  Re-transcribe",
               "Overwrite output for a completed file"),
        ("5",  "🧠  Model Management",
               "Download / switch Whisper model"),
        ("6",  "🌐  Change Language",
               f"Current: {language if language else 'auto-detect'}"),
        ("7",  "⚡  Switch CPU / GPU",
               f"Current: {'GPU (CUDA)' if device == 'cuda' else 'CPU'}"),
        ("8",  f"{'⬇' if translate else '⬆'}  Translation mode",
               f"Translate audio → English  [{_bool_label(translate)}]"),
        ("9",  f"{'⬇' if recursive else '↗'}  Recursive scan",
               f"Include sub-folders in source  [{_bool_label(recursive)}]"),
        ("10", "📄  Export formats",
               f"TXT [{_bool_label(export_txt)}]  SRT [{_bool_label(export_srt)}]  VTT [{_bool_label(export_vtt)}]"),
        ("11", "🔍  Environment Check",
               "Re-check dependencies"),
        ("12", "📂  Open Folders",
               "Open source / output folder"),
        ("0",  "🚪  Exit",
               ""),
    ]

    for key, title, desc in items:
        if desc:
            print(f"  {BRIGHT}{CYAN}[{key:>2}]{RESET}  {title}")
            print(f"         {DIM}{desc}{RESET}")
        else:
            print(f"  {BRIGHT}{CYAN}[{key:>2}]{RESET}  {title}")
        print()


# ─── Sub-menus ────────────────────────────────────────────────────────────────

def select_device(current_device: str) -> str:
    """CPU / GPU switching menu."""
    header("Select Transcription Device")
    gpu_info = get_gpu_info()
    cuda_available = gpu_info is not None

    print()
    current_label = "GPU (CUDA)" if current_device == "cuda" else "CPU"
    info(f"Current device: {BRIGHT}{current_label}{RESET}")
    print()

    cpu_marker = f"  {GREEN}← current{RESET}" if current_device == "cpu" else ""
    print(f"  {BRIGHT}{CYAN}[1]{RESET}  💻  CPU (Central Processing Unit){cpu_marker}")
    print(f"       {DIM}Always available. Works with any model.{RESET}")
    print()

    if cuda_available:
        gpu_marker = f"  {GREEN}← current{RESET}" if current_device == "cuda" else ""
        vram = gpu_info["memory_gb"]
        print(f"  {BRIGHT}{CYAN}[2]{RESET}  ⚡  GPU — {BRIGHT}{gpu_info['name']}{RESET} "
              f"({vram} GB VRAM){gpu_marker}")
        print(f"       {DIM}5-10× faster than CPU. CUDA {gpu_info['cuda_version']}. Recommended!{RESET}")
        if vram < 4:
            print(f"       {YELLOW}⚠ Low VRAM — use: tiny, base, small{RESET}")
        elif vram < 8:
            print(f"       {DIM}Recommended: up to medium{RESET}")
    else:
        print(f"  {RED}[2]{RESET}  ⚡  GPU — {RED}Not available{RESET}")
        print(f"       {DIM}CUDA not detected. PyTorch+CUDA required.{RESET}")

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
    """Language selection menu."""
    header("Transcription Language")

    languages = [
        ("auto", "Auto-detect (recommended)"),
        ("en",   "English"),
        ("ru",   "Russian"),
        ("uk",   "Ukrainian"),
        ("de",   "German"),
        ("fr",   "French"),
        ("es",   "Spanish"),
        ("it",   "Italian"),
        ("ja",   "Japanese"),
        ("zh",   "Chinese"),
        ("ko",   "Korean"),
        ("pt",   "Portuguese"),
        ("ar",   "Arabic"),
        ("hi",   "Hindi"),
        ("tr",   "Turkish"),
        ("pl",   "Polish"),
        ("nl",   "Dutch"),
        ("sv",   "Swedish"),
        ("no",   "Norwegian"),
        ("fi",   "Finnish"),
        ("cs",   "Czech"),
        ("sk",   "Slovak"),
        ("ro",   "Romanian"),
        ("hu",   "Hungarian"),
        ("bg",   "Bulgarian"),
    ]

    current_display = current if current else "auto"
    info(f"Current language: {BRIGHT}{current_display}{RESET}")
    print()

    for i, (code, name) in enumerate(languages):
        marker = (f"  {GREEN}← current{RESET}"
                  if (code == current or (code == "auto" and current is None)) else "")
        bullet(f"{name} ({code}){marker}", i)

    print()
    try:
        choice = int(input("  Select option: ").strip())
        if 0 <= choice < len(languages):
            code = languages[choice][0]
            selected = None if code == "auto" else code
            success(f"Language set: {languages[choice][1]}")
            return selected
    except (ValueError, IndexError):
        pass

    warning("Language unchanged.")
    return current


def toggle_translate(current: bool) -> bool:
    """Toggle translation mode."""
    header("Translation Mode")
    info("When ON, Whisper translates any language → English text.")
    info("When OFF, Whisper transcribes in the original language.")
    print()
    current_label = f"{GREEN}ON{RESET}" if current else f"{RED}OFF{RESET}"
    info(f"Current: {current_label}")
    print()
    if confirm("Toggle translation mode?"):
        new_val = not current
        label = f"{GREEN}ON{RESET}" if new_val else f"{RED}OFF{RESET}"
        success(f"Translation mode: {label}")
        return new_val
    info("Unchanged.")
    return current


def toggle_recursive(current: bool) -> bool:
    """Toggle recursive folder scanning."""
    header("Recursive Folder Scan")
    info("When ON, sub-folders inside source/ are also scanned.")
    print()
    current_label = f"{GREEN}ON{RESET}" if current else f"{RED}OFF{RESET}"
    info(f"Current: {current_label}")
    print()
    if confirm("Toggle recursive scan?"):
        new_val = not current
        label = f"{GREEN}ON{RESET}" if new_val else f"{RED}OFF{RESET}"
        success(f"Recursive scan: {label}")
        return new_val
    info("Unchanged.")
    return current


def select_export_formats(
    export_txt: bool, export_srt: bool, export_vtt: bool
) -> tuple[bool, bool, bool]:
    """Toggle which output formats to generate."""
    header("Export Formats")

    formats = [
        ("txt", export_txt,
         "Plain text + timestamps — human-readable"),
        ("srt", export_srt,
         "SubRip subtitles — supported by most video players"),
        ("vtt", export_vtt,
         "WebVTT subtitles — used by HTML5 video, YouTube, etc."),
    ]

    info("At least one format must remain ON.")
    print()

    for code, flag, desc in formats:
        label = f"{GREEN}ON {RESET}" if flag else f"{RED}OFF{RESET}"
        print(f"  {BRIGHT}{code.upper():<4}{RESET}  [{label}]  {DIM}{desc}{RESET}")
    print()

    result = {
        "txt": export_txt,
        "srt": export_srt,
        "vtt": export_vtt,
    }

    print(f"  Enter format codes to toggle (e.g.  txt  or  srt vtt  or  all)")
    choice = input("  Toggle: ").strip().lower()

    if choice in ("all", "a"):
        # Flip all
        flip = not all([export_txt, export_srt, export_vtt])
        result = {"txt": flip, "srt": flip, "vtt": flip}
    else:
        tokens = choice.split()
        for token in tokens:
            if token in result:
                result[token] = not result[token]

    # Ensure at least one format remains active
    if not any(result.values()):
        warning("At least one format must be ON — resetting to defaults.")
        return True, True, True

    for code, flag in result.items():
        label = f"{GREEN}ON {RESET}" if flag else f"{RED}OFF{RESET}"
        print(f"  {BRIGHT}{code.upper()}{RESET}  →  [{label}]")

    return result["txt"], result["srt"], result["vtt"]


def open_folders(state: dict):
    """Open folders and set custom paths."""
    header("Folders")

    src = get_source_dir()
    out = get_output_dir()
    src_custom = src != _DEFAULT_SOURCE_DIR
    out_custom = out != _DEFAULT_OUTPUT_DIR

    print()
    info(f"Source: {BRIGHT}{src}{RESET}"
         + (f"  {YELLOW}(custom){RESET}" if src_custom else ""))
    info(f"Output: {BRIGHT}{out}{RESET}"
         + (f"  {YELLOW}(custom){RESET}" if out_custom else ""))
    print()

    bullet("Open source folder in explorer", 1)
    bullet("Open output folder in explorer", 2)
    bullet("Open both folders", 3)
    print()
    bullet("Set custom source folder", 4)
    bullet("Set custom output folder", 5)
    if src_custom or out_custom:
        bullet("Reset to default folders", 6)
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
        _set_custom_folder("source", state)
    elif choice == "5":
        _set_custom_folder("output", state)
    elif choice == "6" and (src_custom or out_custom):
        reset_source_dir()
        reset_output_dir()
        success("Reset to defaults:")
        info(f"  Source: {get_source_dir()}")
        info(f"  Output: {get_output_dir()}")
        save_settings(_state_to_settings(state))


def _set_custom_folder(folder_type: str, state: dict):
    """Set a custom source or output folder path."""
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

    save_settings(_state_to_settings(state))
    success(f"{folder_type.capitalize()} folder set: {BRIGHT}{path}{RESET}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Main application function."""
    clear_screen()
    banner(APP_NAME, APP_VERSION)

    # 1. Load persisted settings
    settings = load_settings()
    if settings.get("source_dir"):
        set_source_dir(settings["source_dir"])
    if settings.get("output_dir"):
        set_output_dir(settings["output_dir"])

    # 2. Create directories
    ensure_directories()

    # 3. Environment check
    from checks import run_startup_checks
    if not run_startup_checks():
        if not confirm("Continue despite errors?"):
            sys.exit(1)

    # 4. Device detection
    saved_device = settings.get("device", "auto")
    device = resolve_device(saved_device)
    gpu_info = get_gpu_info()
    header("Transcription Device")
    if device == "cuda" and gpu_info:
        success(f"⚡ GPU: {gpu_info['name']} ({gpu_info['memory_gb']} GB VRAM)")
        info("Model will be loaded on GPU for maximum speed.")
    else:
        info("💻 Using CPU. Switch to GPU via menu option 7.")

    # 5. Model check & load
    from model_manager import (
        check_model_on_startup, load_model, show_models_menu,
    )

    current_model_name = settings.get("model") or check_model_on_startup()
    from model_manager import is_model_downloaded
    if current_model_name and not is_model_downloaded(current_model_name):
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

    # 6. Runtime state
    state: dict = {
        "model_name":   current_model_name,
        "model_loaded": model_loaded,
        "device":       device,
        "language":     settings.get("language"),
        "translate":    settings.get("translate", False),
        "recursive":    settings.get("recursive", False),
        "export_txt":   settings.get("export_txt", True),
        "export_srt":   settings.get("export_srt", True),
        "export_vtt":   settings.get("export_vtt", True),
    }

    save_settings(_state_to_settings(state))

    # 7. Import transcription functions
    from transcriber import (
        show_files_status, transcribe_all, transcribe_selected, retranscribe_file,
    )

    # ── Main menu loop ─────────────────────────────────────────────────────────
    while True:
        show_main_menu(state)
        choice = input(f"  {BRIGHT}Your choice:{RESET} ").strip()

        # ① File status
        if choice == "1":
            show_files_status(
                recursive=state["recursive"],
                export_txt=state["export_txt"],
                export_srt=state["export_srt"],
                export_vtt=state["export_vtt"],
            )

        # ② Transcribe all
        elif choice == "2":
            if not model_loaded:
                error("Load a model first! (option 5)")
            else:
                transcribe_all(
                    model,
                    language=state["language"],
                    translate=state["translate"],
                    recursive=state["recursive"],
                    export_txt=state["export_txt"],
                    export_srt=state["export_srt"],
                    export_vtt=state["export_vtt"],
                )

        # ③ Select files
        elif choice == "3":
            if not model_loaded:
                error("Load a model first! (option 5)")
            else:
                transcribe_selected(
                    model,
                    language=state["language"],
                    translate=state["translate"],
                    recursive=state["recursive"],
                    export_txt=state["export_txt"],
                    export_srt=state["export_srt"],
                    export_vtt=state["export_vtt"],
                )

        # ④ Re-transcribe
        elif choice == "4":
            if not model_loaded:
                error("Load a model first! (option 5)")
            else:
                retranscribe_file(
                    model,
                    language=state["language"],
                    translate=state["translate"],
                    recursive=state["recursive"],
                    export_txt=state["export_txt"],
                    export_srt=state["export_srt"],
                    export_vtt=state["export_vtt"],
                )

        # ⑤ Model management
        elif choice == "5":
            result = show_models_menu()
            if result:
                try:
                    model = load_model(result, device=device)
                    current_model_name      = result
                    model_loaded            = True
                    state["model_name"]     = result
                    state["model_loaded"]   = True
                    save_settings(_state_to_settings(state))
                except Exception as e:
                    error(f"Failed to load model: {e}")

        # ⑥ Language
        elif choice == "6":
            state["language"] = select_language(state["language"])
            save_settings(_state_to_settings(state))

        # ⑦ CPU / GPU
        elif choice == "7":
            new_device = select_device(device)
            if new_device != device:
                device          = new_device
                state["device"] = new_device
                if model_loaded and current_model_name:
                    info("Reloading model on new device...")
                    try:
                        model        = load_model(current_model_name, device=device)
                        model_loaded = True
                        success("Model reloaded!")
                    except Exception as e:
                        error(f"Error: {e}")
                        if device == "cuda":
                            warning("Falling back to CPU...")
                            device          = "cpu"
                            state["device"] = "cpu"
                            try:
                                model = load_model(current_model_name, device="cpu")
                            except Exception:
                                model_loaded = False
                                state["model_loaded"] = False
                save_settings(_state_to_settings(state))

        # ⑧ Translation mode toggle
        elif choice == "8":
            state["translate"] = toggle_translate(state["translate"])
            save_settings(_state_to_settings(state))

        # ⑨ Recursive scan toggle
        elif choice == "9":
            state["recursive"] = toggle_recursive(state["recursive"])
            save_settings(_state_to_settings(state))

        # ⑩ Export formats
        elif choice == "10":
            state["export_txt"], state["export_srt"], state["export_vtt"] = (
                select_export_formats(
                    state["export_txt"], state["export_srt"], state["export_vtt"]
                )
            )
            save_settings(_state_to_settings(state))

        # ⑪ Environment check
        elif choice == "11":
            from checks import run_startup_checks
            run_startup_checks()

        # ⑫ Open folders
        elif choice == "12":
            open_folders(state)

        # ⓪ Exit
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
