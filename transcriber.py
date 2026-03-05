"""
Transcription engine — video file processing
"""
import os
import time
import traceback

from config import get_source_dir, get_output_dir, VIDEO_EXTENSIONS, DEFAULT_LANGUAGE
from ui import (
    info, success, warning, error, header, bullet, confirm,
    format_duration, format_size, progress_bar_simple,
    BRIGHT, CYAN, GREEN, YELLOW, RED, RESET, DIM
)


def scan_source_folder() -> list[dict]:
    """Scan source folder for video files"""
    source = get_source_dir()
    if not os.path.exists(source):
        return []

    files = []
    for f in sorted(os.listdir(source)):
        ext = os.path.splitext(f)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            full_path = os.path.join(source, f)
            files.append({
                "name": f,
                "path": full_path,
                "size": os.path.getsize(full_path),
                "ext": ext,
                "basename": os.path.splitext(f)[0],
            })
    return files


def get_pending_files(files: list[dict]) -> list[dict]:
    """Get list of files not yet transcribed"""
    pending = []
    for f in files:
        output_path = os.path.join(get_output_dir(), f["basename"] + ".txt")
        if not os.path.exists(output_path):
            pending.append(f)
    return pending


def get_completed_files(files: list[dict]) -> list[dict]:
    """Get list of already processed files"""
    completed = []
    for f in files:
        output_path = os.path.join(get_output_dir(), f["basename"] + ".txt")
        if os.path.exists(output_path):
            completed.append(f)
    return completed


def show_files_status():
    """Show status of all files"""
    header("File Status")
    info(f"Source: {get_source_dir()}")
    info(f"Output: {get_output_dir()}")

    files = scan_source_folder()
    if not files:
        warning("The source folder is empty or contains no video files.")
        info(f"Supported formats: {', '.join(sorted(VIDEO_EXTENSIONS))}")
        return

    pending = get_pending_files(files)
    completed = get_completed_files(files)

    print(f"\n  Total videos:    {BRIGHT}{len(files)}{RESET}")
    print(f"  Transcribed:     {BRIGHT}{GREEN}{len(completed)}{RESET}")
    print(f"  Pending:         {BRIGHT}{YELLOW}{len(pending)}{RESET}\n")

    for f in files:
        size = format_size(f["size"])
        output_path = os.path.join(get_output_dir(), f["basename"] + ".txt")
        if os.path.exists(output_path):
            status = f"{GREEN}✔ done{RESET}"
        else:
            status = f"{YELLOW}○ pending{RESET}"
        print(f"    {status}  {BRIGHT}{f['name']:<45}{RESET}  {DIM}{size}{RESET}")

    print()


def transcribe_file(model, file_info: dict, language: str | None = None) -> bool:
    """Transcribe a single file"""
    output_path = os.path.join(get_output_dir(), file_info["basename"] + ".txt")

    try:
        # Detect model device
        device = str(next(model.parameters()).device)
        is_gpu = "cuda" in device
        device_label = f"GPU ({device})" if is_gpu else "CPU"

        info(f"Transcribing: {BRIGHT}{file_info['name']}{RESET}")
        info(f"Size: {format_size(file_info['size'])}  |  Device: {device_label}")

        start_time = time.time()

        # Transcription settings
        # fp16=True for GPU (faster), fp16=False for CPU (no fp16 support)
        options = {
            "verbose": False,
            "fp16": is_gpu,
        }
        if language:
            options["language"] = language

        result = model.transcribe(file_info["path"], **options)

        elapsed = time.time() - start_time

        # Save result
        text = result["text"].strip()
        detected_lang = result.get("language", "?")

        with open(output_path, "w", encoding="utf-8") as out:
            out.write(f"# Transcription: {file_info['name']}\n")
            out.write(f"# Language: {detected_lang}\n")
            out.write(f"# Processing time: {format_duration(elapsed)}\n")
            out.write(f"# {'=' * 60}\n\n")
            out.write(text + "\n\n")

            # Write segments with timestamps
            out.write(f"# {'=' * 60}\n")
            out.write(f"# Segmented transcription with timestamps:\n")
            out.write(f"# {'=' * 60}\n\n")
            for seg in result.get("segments", []):
                start = format_timestamp(seg["start"])
                end = format_timestamp(seg["end"])
                seg_text = seg["text"].strip()
                out.write(f"[{start} --> {end}]  {seg_text}\n")

        success(f"Done in {format_duration(elapsed)} | Language: {detected_lang}")
        success(f"Saved: {output_path}")
        return True

    except Exception as e:
        error(f"Transcription error {file_info['name']}: {e}")
        traceback.print_exc()
        return False


def format_timestamp(seconds: float) -> str:
    """Format timestamp HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def transcribe_all(model, language: str | None = None) -> tuple[int, int]:
    """Transcribe all pending files"""
    header("Batch Transcription")

    files = scan_source_folder()
    pending = get_pending_files(files)

    if not pending:
        success("All video files are already transcribed!")
        return 0, 0

    total = len(pending)
    info(f"Files to process: {BRIGHT}{total}{RESET}")
    total_size = sum(f["size"] for f in pending)
    info(f"Total size: {format_size(total_size)}")
    print()

    if not confirm("Start transcription?"):
        return 0, 0

    print()
    ok_count = 0
    fail_count = 0

    for i, f in enumerate(pending, 1):
        print(f"\n  {BRIGHT}{CYAN}[{i}/{total}]{RESET} ──────────────────────────────────")
        if transcribe_file(model, f, language):
            ok_count += 1
        else:
            fail_count += 1
        progress_bar_simple(i, total, f"{ok_count} ✔  {fail_count} ✖")

    print()
    header("Results")
    success(f"Succeeded: {ok_count}")
    if fail_count:
        error(f"Failed: {fail_count}")
    return ok_count, fail_count


def transcribe_selected(model, language: str | None = None):
    """Select and transcribe specific files"""
    header("Select Files to Transcribe")

    files = scan_source_folder()
    pending = get_pending_files(files)

    if not pending:
        success("All video files are already transcribed!")
        return

    print()
    for i, f in enumerate(pending, 1):
        size = format_size(f["size"])
        bullet(f"{f['name']}  ({size})", i)

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back")
    print(f"  {BRIGHT}{CYAN}[a]{RESET}  Select all")
    print()

    choice = input("  Enter numbers separated by commas (or 'a' for all, 0 — back): ").strip()
    if choice == "0":
        return
    if choice.lower() == "a":
        transcribe_all(model, language)
        return

    try:
        indices = [int(x.strip()) - 1 for x in choice.split(",")]
        selected = [pending[i] for i in indices if 0 <= i < len(pending)]
    except (ValueError, IndexError):
        error("Invalid input.")
        return

    if not selected:
        warning("No files selected.")
        return

    print()
    info(f"Selected files: {len(selected)}")

    ok = 0
    fail = 0
    for i, f in enumerate(selected, 1):
        print(f"\n  {BRIGHT}{CYAN}[{i}/{len(selected)}]{RESET} ──────────────────────────────────")
        if transcribe_file(model, f, language):
            ok += 1
        else:
            fail += 1

    print()
    header("Results")
    success(f"Succeeded: {ok}")
    if fail:
        error(f"Failed: {fail}")


def retranscribe_file(model, language: str | None = None):
    """Re-transcribe an already processed file"""
    header("Re-transcription")

    files = scan_source_folder()
    completed = get_completed_files(files)

    if not completed:
        warning("No processed files available for re-transcription.")
        return

    print()
    for i, f in enumerate(completed, 1):
        bullet(f"{f['name']}", i)

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back\n")

    try:
        choice = int(input("  Select file: ").strip())
        if choice == 0:
            return
        idx = choice - 1
        if 0 <= idx < len(completed):
            f = completed[idx]
            output_path = os.path.join(get_output_dir(), f["basename"] + ".txt")
            warning(f"File {f['basename']}.txt will be overwritten!")
            if confirm("Continue?"):
                os.remove(output_path)
                transcribe_file(model, f, language)
    except (ValueError, IndexError):
        error("Invalid input.")
