#!/usr/bin/env python3
"""Install these dotfiles into the home directory on Linux, macOS or Windows.

Runs inside ./.venv (created on first run), links every file under home/ into ~
and makes bash and zsh load ~/.bash_aliases. Safe to re-run.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()
VENV = REPO / ".venv"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

SOURCE_ALIASES = "[ -f ~/.bash_aliases ] && . ~/.bash_aliases"
SOURCE_BASHRC = '[ -n "$BASH_VERSION" ] && [ -f ~/.bashrc ] && . ~/.bashrc'


def run_in_venv():
    """Create .venv on first run, then re-execute this script with its interpreter."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    if not VENV_PYTHON.exists():
        print("creating", VENV, flush=True)
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
        subprocess.check_call([str(VENV_PYTHON), "-m", "pip", "install", "-q", "-r", str(REPO / "requirements.txt")])
    sys.exit(subprocess.call([str(VENV_PYTHON), str(REPO / "install.py")] + sys.argv[1:]))


def install(src, dst):
    """Symlink dst -> src, or copy where symlinks are refused (Windows). Keeps a .bak of what was there."""
    if (dst.is_symlink() and dst.resolve() == src) or (dst.is_file() and dst.read_bytes() == src.read_bytes()):
        return
    if dst.is_symlink() or dst.exists():
        dst.replace(dst.with_name(dst.name + ".bak"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    print("installed", dst)


def ensure_line(rc, line, mentions):
    """Append line to rc unless rc already mentions the file it sources."""
    text = rc.read_text(encoding="utf-8") if rc.exists() else ""
    if mentions not in text:
        with rc.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n" + line + "\n")
        print("updated", rc)


def main():
    run_in_venv()

    for src in sorted(p for p in (REPO / "home").rglob("*") if p.is_file()):
        if not src.name.endswith((".swp", ".swo", "~")):
            install(src, HOME / src.relative_to(REPO / "home"))

    ensure_line(HOME / ".bashrc", SOURCE_ALIASES, ".bash_aliases")
    if sys.platform == "darwin" or shutil.which("zsh"):
        ensure_line(HOME / ".zshrc", SOURCE_ALIASES, ".bash_aliases")

    # Login shells (macOS Terminal, Git Bash) read the first of these instead of .bashrc.
    profiles = [HOME / n for n in (".bash_profile", ".bash_login", ".profile")]
    ensure_line(next((p for p in profiles if p.exists()), profiles[-1]), SOURCE_BASHRC, ".bashrc")

    print("done, open a new terminal")


if __name__ == "__main__":
    main()
