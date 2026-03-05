"""
Console output utilities and common helpers
"""
import os
import sys
import shutil

from colorama import init, Fore, Back, Style

init(autoreset=True)

# ─── Colors and styles ──────────────────────────────────────────────────────
CYAN = Fore.CYAN
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
MAGENTA = Fore.MAGENTA
WHITE = Fore.WHITE
DIM = Style.DIM
BRIGHT = Style.BRIGHT
RESET = Style.RESET_ALL

TERM_WIDTH = shutil.get_terminal_size((80, 24)).columns


def banner(app_name: str, version: str):
    """Render ASCII banner"""
    line = "═" * (TERM_WIDTH - 2)
    print(f"\n{CYAN}╔{line}╗")
    title = f"  🎙  {app_name} v{version}  — Video Transcription powered by Whisper  "
    pad = TERM_WIDTH - 2 - len(title) + len(CYAN) + len(BRIGHT)
    print(f"{CYAN}║{BRIGHT}{WHITE}{title}{' ' * max(pad, 0)}{CYAN}║")
    print(f"{CYAN}╚{line}╝{RESET}\n")


def header(text: str):
    """Section header"""
    print(f"\n{BRIGHT}{MAGENTA}{'─' * 3} {text} {'─' * (TERM_WIDTH - len(text) - 6)}{RESET}")


def info(text: str):
    print(f"  {CYAN}ℹ{RESET}  {text}")


def success(text: str):
    print(f"  {GREEN}✔{RESET}  {text}")


def warning(text: str):
    print(f"  {YELLOW}⚠{RESET}  {text}")


def error(text: str):
    print(f"  {RED}✖{RESET}  {text}")


def bullet(text: str, index: int | None = None):
    if index is not None:
        print(f"  {BRIGHT}{CYAN}[{index}]{RESET}  {text}")
    else:
        print(f"  {DIM}•{RESET}  {text}")


def progress_bar_simple(current: int, total: int, label: str = ""):
    """Simple progress bar without tqdm"""
    pct = current / total if total > 0 else 0
    bar_len = 30
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stdout.write(f"\r  {GREEN}{bar}{RESET}  {pct * 100:5.1f}%  {label}")
    if current >= total:
        sys.stdout.write("\n")
    sys.stdout.flush()


def confirm(prompt: str) -> bool:
    """Ask user for confirmation"""
    while True:
        ans = input(f"  {YELLOW}?{RESET}  {prompt} (y/n): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


def format_duration(seconds: float) -> str:
    """Format duration"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def format_size(size_bytes: int) -> str:
    """Format file size"""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
