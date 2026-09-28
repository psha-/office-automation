#!/usr/bin/env python3
"""Install these dotfiles into the home directory on Linux, macOS or Windows.

Links every file under home/ into ~
and makes bash and zsh load ~/.bash_aliases. Safe to re-run.
"""
import itertools
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOME = Path.home()

SOURCE_ALIASES = "[ -f ~/.bash_aliases ] && . ~/.bash_aliases"
SOURCE_BASHRC = '[ -n "$BASH_VERSION" ] && [ -f ~/.bashrc ] && . ~/.bashrc'


def can_symlink():
    """Whether this user may create symlinks. Windows refuses unless Developer Mode is on."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "target"
        target.touch()
        try:
            os.symlink(target, Path(tmp) / "link")
        except OSError:
            return False
    return True


def backup_name(path):
    """First free name among path.bak, path.bak1, path.bak2, ..."""
    for i in itertools.count():
        candidate = path.with_name(f"{path.name}.bak{i or ''}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate


def install(dst, src, link):
    """Symlink dst -> src, or copy when link is False. Keeps a .bak of what was there."""
    if dst.is_symlink():
        if dst.resolve() == src:
            return
    elif not link and dst.is_file() and dst.read_bytes() == src.read_bytes():
        return

    if dst.is_symlink() or dst.exists():
        bak = backup_name(dst)
        dst.replace(bak)
        print("backed up", dst, "as", bak.name)

    dst.parent.mkdir(parents=True, exist_ok=True)
    if link:
        os.symlink(src, dst)
    else:
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
    link = can_symlink()
    if not link:
        print("symlinks refused, copying instead")

    for src in sorted(p for p in (REPO / "home").rglob("*") if p.is_file()):
        if not src.name.endswith((".swp", ".swo", "~")):
            install(HOME / src.relative_to(REPO / "home"), src, link)

    ensure_line(HOME / ".bashrc", SOURCE_ALIASES, ".bash_aliases")
    if sys.platform == "darwin" or shutil.which("zsh"):
        ensure_line(HOME / ".zshrc", SOURCE_ALIASES, ".bash_aliases")

    # Login shells (macOS Terminal, Git Bash) read the first of these instead of .bashrc.
    profiles = [HOME / n for n in (".bash_profile", ".bash_login", ".profile")]
    ensure_line(next((p for p in profiles if p.exists()), profiles[-1]), SOURCE_BASHRC, ".bashrc")

    print("done, open a new terminal")


if __name__ == "__main__":
    main()
