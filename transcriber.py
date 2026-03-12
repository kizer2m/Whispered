"""
Transcription engine — video & audio file processing
"""
import os
import time
import traceback

from config import (
    get_source_dir, get_output_dir,
    ALL_MEDIA_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS,
)
from ui import (
    info, success, warning, error, header, bullet, confirm,
    format_duration, format_eta, format_size, progress_bar_simple,
    BRIGHT, CYAN, GREEN, YELLOW, RED, RESET, DIM,
)


# ─── Timestamp helpers ───────────────────────────────────────────────────────

def _ts_plain(seconds: float) -> str:
    """HH:MM:SS.mmm (for .txt)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _ts_srt(seconds: float) -> str:
    """HH:MM:SS,mmm (SRT uses comma)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ts_vtt(seconds: float) -> str:
    """HH:MM:SS.mmm (WebVTT)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


# ─── File scanning ───────────────────────────────────────────────────────────

def scan_source_folder(recursive: bool = False) -> list[dict]:
    """Scan source folder for media files.

    Args:
        recursive: If True, also scans sub-folders.

    Returns:
        List of file info dicts sorted by path.
    """
    source = get_source_dir()
    if not os.path.exists(source):
        return []

    files = []

    walk_fn = os.walk(source) if recursive else _single_dir_walk(source)
    for dirpath, _, filenames in walk_fn:
        for fname in sorted(filenames):
            ext = os.path.splitext(fname)[1].lower()
            if ext in ALL_MEDIA_EXTENSIONS:
                full_path = os.path.join(dirpath, fname)
                # Relative path fragment (empty for root)
                rel_dir = os.path.relpath(dirpath, source)
                rel_dir = "" if rel_dir == "." else rel_dir
                # Use relative path as display name for nested files
                display = os.path.join(rel_dir, fname) if rel_dir else fname
                files.append({
                    "name":     display,
                    "path":     full_path,
                    "size":     os.path.getsize(full_path),
                    "ext":      ext,
                    "basename": os.path.splitext(display.replace(os.sep, "_"))[0],
                    "is_audio": ext in AUDIO_EXTENSIONS,
                })

    return files


def _single_dir_walk(path: str):
    """Yields a single (dirpath, dirs, files) tuple — non-recursive."""
    try:
        entries = os.listdir(path)
    except PermissionError:
        return
    files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
    yield path, [], files


def _is_done(f: dict, export_txt: bool, export_srt: bool, export_vtt: bool) -> bool:
    """Return True if all requested outputs already exist."""
    out_dir = get_output_dir()
    base = f["basename"]
    checks = []
    if export_txt:
        checks.append(os.path.join(out_dir, base + ".txt"))
    if export_srt:
        checks.append(os.path.join(out_dir, base + ".srt"))
    if export_vtt:
        checks.append(os.path.join(out_dir, base + ".vtt"))
    # At least one output expected; consider done if ALL expected outputs exist
    return bool(checks) and all(os.path.exists(p) for p in checks)


def get_pending_files(
    files: list[dict],
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
) -> list[dict]:
    return [f for f in files if not _is_done(f, export_txt, export_srt, export_vtt)]


def get_completed_files(
    files: list[dict],
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
) -> list[dict]:
    return [f for f in files if _is_done(f, export_txt, export_srt, export_vtt)]


# ─── Status display ──────────────────────────────────────────────────────────

def show_files_status(recursive: bool = False,
                      export_txt: bool = True,
                      export_srt: bool = True,
                      export_vtt: bool = True):
    """Show status of all media files in source folder."""
    header("File Status")
    info(f"Source: {get_source_dir()}")
    info(f"Output: {get_output_dir()}")
    if recursive:
        info("Recursive scan: ON")

    files = scan_source_folder(recursive=recursive)
    if not files:
        warning("The source folder is empty or contains no supported media files.")
        exts = ", ".join(sorted(ALL_MEDIA_EXTENSIONS))
        info(f"Supported formats: {exts}")
        return

    pending   = get_pending_files(files, export_txt, export_srt, export_vtt)
    completed = get_completed_files(files, export_txt, export_srt, export_vtt)

    video_count = sum(1 for f in files if not f["is_audio"])
    audio_count = sum(1 for f in files if f["is_audio"])

    print(f"\n  Media files:     {BRIGHT}{len(files)}{RESET}"
          f"  ({video_count} video, {audio_count} audio)")
    print(f"  Transcribed:     {BRIGHT}{GREEN}{len(completed)}{RESET}")
    print(f"  Pending:         {BRIGHT}{YELLOW}{len(pending)}{RESET}\n")

    # Exports column header
    fmt_cols = []
    if export_txt: fmt_cols.append("TXT")
    if export_srt: fmt_cols.append("SRT")
    if export_vtt: fmt_cols.append("VTT")
    fmt_header = "/".join(fmt_cols) if fmt_cols else "—"
    print(f"    {'Status':<10}  {'File':<45}  {'Size':>8}  {fmt_header}")
    print(f"    {'─'*10}  {'─'*45}  {'─'*8}  {'─'*len(fmt_header)}")

    for f in files:
        out_dir  = get_output_dir()
        base     = f["basename"]
        has_txt  = os.path.exists(os.path.join(out_dir, base + ".txt"))
        has_srt  = os.path.exists(os.path.join(out_dir, base + ".srt"))
        has_vtt  = os.path.exists(os.path.join(out_dir, base + ".vtt"))

        done = _is_done(f, export_txt, export_srt, export_vtt)
        status = f"{GREEN}✔ done{RESET}" if done else f"{YELLOW}○ pending{RESET}"

        # Per-format indicators
        def _ind(flag: bool, present: bool) -> str:
            if not flag: return ""
            return f"{GREEN}✔{RESET}" if present else f"{RED}✖{RESET}"

        fmt_ind = "/".join(filter(None, [
            _ind(export_txt, has_txt),
            _ind(export_srt, has_srt),
            _ind(export_vtt, has_vtt),
        ]))

        icon = "♪" if f["is_audio"] else "▶"
        size = format_size(f["size"])
        print(f"    {status:<10}  {icon} {BRIGHT}{f['name']:<43}{RESET}  "
              f"{DIM}{size:>8}{RESET}  {fmt_ind}")

    print()


# ─── Export helpers ──────────────────────────────────────────────────────────

def _write_txt(path: str, file_name: str, lang: str, elapsed: float,
               text: str, segments: list, translate: bool):
    mode = "Translation → English" if translate else "Transcription"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {mode}: {file_name}\n")
        f.write(f"# Language: {lang}\n")
        f.write(f"# Processing time: {format_duration(elapsed)}\n")
        f.write(f"# {'=' * 60}\n\n")
        f.write(text + "\n\n")
        f.write(f"# {'=' * 60}\n")
        f.write(f"# Segmented transcription with timestamps:\n")
        f.write(f"# {'=' * 60}\n\n")
        for seg in segments:
            s = _ts_plain(seg["start"])
            e = _ts_plain(seg["end"])
            f.write(f"[{s} --> {e}]  {seg['text'].strip()}\n")


def _write_srt(path: str, segments: list):
    with open(path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, 1):
            f.write(f"{idx}\n")
            f.write(f"{_ts_srt(seg['start'])} --> {_ts_srt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def _write_vtt(path: str, segments: list):
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for idx, seg in enumerate(segments, 1):
            f.write(f"{idx}\n")
            f.write(f"{_ts_vtt(seg['start'])} --> {_ts_vtt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


# ─── Core transcription ──────────────────────────────────────────────────────

def transcribe_file(
    model,
    file_info: dict,
    language: str | None = None,
    translate: bool = False,
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
) -> bool:
    """Transcribe (or translate) a single media file and write requested outputs.

    Args:
        model:      Loaded Whisper model.
        file_info:  Dict from scan_source_folder().
        language:   BCP-47 language code or None for auto-detect.
        translate:  If True, Whisper translates audio → English text.
        export_txt: Write a human-readable .txt file.
        export_srt: Write a SubRip .srt subtitle file.
        export_vtt: Write a WebVTT .vtt subtitle file.

    Returns:
        True on success, False on failure.
    """
    if not any([export_txt, export_srt, export_vtt]):
        warning("No output formats selected — skipping.")
        return False

    out_dir  = get_output_dir()
    base     = file_info["basename"]
    txt_path = os.path.join(out_dir, base + ".txt")
    srt_path = os.path.join(out_dir, base + ".srt")
    vtt_path = os.path.join(out_dir, base + ".vtt")

    try:
        device    = str(next(model.parameters()).device)
        is_gpu    = "cuda" in device
        dev_label = f"GPU ({device})" if is_gpu else "CPU"
        icon      = "♪" if file_info["is_audio"] else "▶"

        info(f"{icon} Transcribing: {BRIGHT}{file_info['name']}{RESET}")
        info(f"Size: {format_size(file_info['size'])}  |  Device: {dev_label}"
             + (f"  |  {YELLOW}Translation → EN{RESET}" if translate else ""))

        start_time = time.time()

        options: dict = {
            "verbose": False,
            "fp16":    is_gpu,
            "task":    "translate" if translate else "transcribe",
        }
        if language:
            options["language"] = language

        result = model.transcribe(file_info["path"], **options)

        elapsed      = time.time() - start_time
        text         = result["text"].strip()
        detected_lang = result.get("language", "?")
        segments     = result.get("segments", [])

        # Ensure sub-directory of output exists (for recursive source trees)
        os.makedirs(out_dir, exist_ok=True)

        saved = []
        if export_txt:
            _write_txt(txt_path, file_info["name"], detected_lang,
                       elapsed, text, segments, translate)
            saved.append("txt")
        if export_srt:
            _write_srt(srt_path, segments)
            saved.append("srt")
        if export_vtt:
            _write_vtt(vtt_path, segments)
            saved.append("vtt")

        mode_label = "translated" if translate else "transcribed"
        success(f"Done in {format_duration(elapsed)} | "
                f"Language: {detected_lang} | "
                f"Saved: {', '.join(f'.{s}' for s in saved)}")
        return True

    except Exception as e:
        error(f"Transcription error — {file_info['name']}: {e}")
        traceback.print_exc()
        return False


# ─── Batch operations ────────────────────────────────────────────────────────

def transcribe_all(
    model,
    language: str | None = None,
    translate: bool = False,
    recursive: bool = False,
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
) -> tuple[int, int]:
    """Transcribe all pending media files."""
    header("Batch Transcription")

    files   = scan_source_folder(recursive=recursive)
    pending = get_pending_files(files, export_txt, export_srt, export_vtt)

    if not pending:
        success("All media files are already transcribed!")
        return 0, 0

    total      = len(pending)
    total_size = sum(f["size"] for f in pending)
    info(f"Files to process: {BRIGHT}{total}{RESET}")
    info(f"Total size: {format_size(total_size)}")
    if recursive:
        info("Recursive mode: ON")
    if translate:
        info(f"Mode: {YELLOW}Translate → English{RESET}")
    fmts = [s for s, v in [("txt", export_txt), ("srt", export_srt), ("vtt", export_vtt)] if v]
    info(f"Export formats: {', '.join(f'.{f}' for f in fmts)}")
    print()

    if not confirm("Start transcription?"):
        return 0, 0

    print()
    ok_count   = 0
    fail_count = 0
    batch_start = time.time()

    for i, f in enumerate(pending, 1):
        elapsed_so_far = time.time() - batch_start
        eta = format_eta(elapsed_so_far, i - 1, total)
        print(f"\n  {BRIGHT}{CYAN}[{i}/{total}]{RESET}  {DIM}{eta}{RESET}"
              f"  ──────────────────────────────────")
        if transcribe_file(model, f, language, translate, export_txt, export_srt, export_vtt):
            ok_count += 1
        else:
            fail_count += 1
        progress_bar_simple(i, total, f"{ok_count} ✔  {fail_count} ✖")

    total_elapsed = time.time() - batch_start
    print()
    header("Batch Results")
    success(f"Succeeded: {ok_count}")
    if fail_count:
        error(f"Failed: {fail_count}")
    success(f"Total time: {format_duration(total_elapsed)}")
    return ok_count, fail_count


def transcribe_selected(
    model,
    language: str | None = None,
    translate: bool = False,
    recursive: bool = False,
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
):
    """Interactively select and transcribe specific files."""
    header("Select Files to Transcribe")

    files   = scan_source_folder(recursive=recursive)
    pending = get_pending_files(files, export_txt, export_srt, export_vtt)

    if not pending:
        success("All media files are already transcribed!")
        return

    print()
    for i, f in enumerate(pending, 1):
        icon = "♪" if f["is_audio"] else "▶"
        size = format_size(f["size"])
        bullet(f"{icon} {f['name']}  ({size})", i)

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back")
    print(f"  {BRIGHT}{CYAN}[a]{RESET}  Select all")
    print()

    choice = input(
        "  Enter numbers separated by commas (or 'a' for all, 0 — back): "
    ).strip()

    if choice == "0":
        return
    if choice.lower() == "a":
        transcribe_all(model, language, translate, recursive, export_txt, export_srt, export_vtt)
        return

    try:
        indices  = [int(x.strip()) - 1 for x in choice.split(",")]
        selected = [pending[i] for i in indices if 0 <= i < len(pending)]
    except (ValueError, IndexError):
        error("Invalid input.")
        return

    if not selected:
        warning("No files selected.")
        return

    print()
    info(f"Selected files: {len(selected)}")
    ok = fail = 0
    batch_start = time.time()

    for i, f in enumerate(selected, 1):
        elapsed_so_far = time.time() - batch_start
        eta = format_eta(elapsed_so_far, i - 1, len(selected))
        print(f"\n  {BRIGHT}{CYAN}[{i}/{len(selected)}]{RESET}  {DIM}{eta}{RESET}"
              f"  ──────────────────────────────────")
        if transcribe_file(model, f, language, translate, export_txt, export_srt, export_vtt):
            ok += 1
        else:
            fail += 1

    print()
    header("Results")
    success(f"Succeeded: {ok}")
    if fail:
        error(f"Failed: {fail}")


def retranscribe_file(
    model,
    language: str | None = None,
    translate: bool = False,
    recursive: bool = False,
    export_txt: bool = True,
    export_srt: bool = True,
    export_vtt: bool = True,
):
    """Re-transcribe an already processed file (overwrites outputs)."""
    header("Re-transcription")

    files     = scan_source_folder(recursive=recursive)
    completed = get_completed_files(files, export_txt, export_srt, export_vtt)

    if not completed:
        warning("No processed files available for re-transcription.")
        return

    print()
    for i, f in enumerate(completed, 1):
        icon = "♪" if f["is_audio"] else "▶"
        bullet(f"{icon} {f['name']}", i)

    print(f"\n  {BRIGHT}{CYAN}[0]{RESET}  Back\n")

    try:
        choice = int(input("  Select file: ").strip())
        if choice == 0:
            return
        idx = choice - 1
        if 0 <= idx < len(completed):
            f        = completed[idx]
            out_dir  = get_output_dir()
            base     = f["basename"]
            to_delete = []
            if export_txt: to_delete.append(os.path.join(out_dir, base + ".txt"))
            if export_srt: to_delete.append(os.path.join(out_dir, base + ".srt"))
            if export_vtt: to_delete.append(os.path.join(out_dir, base + ".vtt"))

            existing = [p for p in to_delete if os.path.exists(p)]
            fnames   = ", ".join(os.path.basename(p) for p in existing)
            warning(f"Will delete: {fnames}")
            if confirm("Continue?"):
                for p in existing:
                    os.remove(p)
                transcribe_file(model, f, language, translate, export_txt, export_srt, export_vtt)
        else:
            error("Invalid selection.")
    except (ValueError, IndexError):
        error("Invalid input.")
