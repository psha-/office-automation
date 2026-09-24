#!/usr/bin/env python3
"""Install the dotfiles in this repository into the current user's home directory.

Portable by design: standard library only, Python 3.6+, Linux/macOS/Windows.
On first run it creates a virtual environment in ``.venv`` next to this file,
installs ``requirements.txt`` into it and re-executes itself there, so any
Python dependency the dotfiles ever need stays out of the system interpreter.
Every file under ``home/`` is mirrored to the same relative path under ``~``,
symlinked where the OS allows it and copied otherwise. Existing files are
backed up before being replaced. Shell rc files are patched so that bash and
zsh load ``~/.bash_aliases`` on every platform, including login shells.
Safe to re-run at any time.

Usage:
    python3 install.py            # install (symlink, fall back to copy)
    python3 install.py --copy     # always copy instead of symlinking
    python3 install.py --dry-run  # print what would happen, change nothing
    python3 install.py --no-venv  # run with the current interpreter
"""

import sys

if sys.version_info < (3, 6):
    sys.exit("install.py needs Python 3.6 or newer")

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = REPO_DIR / "home"
HOME = Path.home()
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = os.name == "nt"

VENV_DIR = REPO_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
REQUIREMENTS = REPO_DIR / "requirements.txt"
## Set on the re-executed process so the bootstrap can never loop.
VENV_GUARD = "DOTFILES_INSTALL_IN_VENV"

## Editor and OS litter that must never be mirrored into the home directory.
IGNORED_PATTERNS = ("*.swp", "*.swo", "*~", ".DS_Store", "Thumbs.db", "*.bak-*")

## Markers wrapping every block this script appends to an rc file.
BLOCK_START = "# >>> dotfiles: {name} >>>"
BLOCK_END = "# <<< dotfiles: {name} <<<"

## Shell snippet that loads the shared aliases, valid in bash and zsh.
SOURCE_ALIASES = [
    "if [ -f ~/.bash_aliases ]; then",
    "    . ~/.bash_aliases",
    "fi",
]

## Shell snippet that makes a bash login shell load ~/.bashrc.
SOURCE_BASHRC = [
    'if [ -n "$BASH_VERSION" ] && [ -f ~/.bashrc ]; then',
    "    . ~/.bashrc",
    "fi",
]


class Installer:
    """Applies the repository to the home directory, honouring dry-run and copy mode."""

    def __init__(self, copy, dry_run):
        self.copy = copy
        self.dry_run = dry_run
        self.stamp = time.strftime("%Y%m%d-%H%M%S")

    def log(self, action, detail):
        prefix = "[dry-run] " if self.dry_run else ""
        print("{}{:<8} {}".format(prefix, action, detail))

    # -- file mirroring -------------------------------------------------------

    def install_all(self):
        """Mirrors every file below SOURCE_ROOT into HOME."""
        if not SOURCE_ROOT.is_dir():
            sys.exit("missing directory: {}".format(SOURCE_ROOT))
        for src in sorted(p for p in SOURCE_ROOT.rglob("*") if p.is_file()):
            if any(src.match(pattern) for pattern in IGNORED_PATTERNS):
                self.log("skip", "{} (editor/OS temp file)".format(src))
                continue
            self.install_file(src, HOME / src.relative_to(SOURCE_ROOT))

    def install_file(self, src, dst):
        """Links or copies one file, backing up whatever is already at dst."""
        if self._already_installed(src, dst):
            self.log("ok", dst)
            return
        self._backup(dst)
        if not self.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
        if not self.copy and self._symlink(src, dst):
            return
        self.log("copy", "{} <- {}".format(dst, src))
        if not self.dry_run:
            shutil.copy2(str(src), str(dst))

    def _already_installed(self, src, dst):
        """True when dst already is what the current mode would produce.

        Copy mode wants a real file with identical content; link mode wants a
        symlink to src. Anything else gets backed up and replaced.
        """
        if self.copy:
            return dst.is_file() and not dst.is_symlink() and dst.read_bytes() == src.read_bytes()
        if dst.is_symlink():
            try:
                return dst.resolve() == src.resolve()
            except OSError:
                return False
        return False

    def _backup(self, dst):
        """Moves an existing file aside; a broken symlink is simply removed."""
        if not dst.is_symlink() and not dst.exists():
            return
        if dst.is_symlink() and not dst.exists():
            self.log("unlink", "{} (broken symlink)".format(dst))
            if not self.dry_run:
                dst.unlink()
            return
        backup = dst.with_name("{}.bak-{}".format(dst.name, self.stamp))
        self.log("backup", "{} -> {}".format(dst, backup))
        if not self.dry_run:
            dst.replace(backup)

    def _symlink(self, src, dst):
        """Creates dst -> src; False when the OS refuses, e.g. Windows without developer mode."""
        self.log("link", "{} -> {}".format(dst, src))
        if self.dry_run:
            return True
        try:
            os.symlink(str(src), str(dst))
            return True
        except (OSError, NotImplementedError) as exc:
            reason = getattr(exc, "strerror", None) or str(exc)
            print("         symlink refused ({}); copying instead".format(reason))
            return False

    # -- shell rc files -------------------------------------------------------

    def configure_shells(self):
        """Makes bash and zsh load ~/.bash_aliases, including from login shells."""
        self.ensure_block(HOME / ".bashrc", "aliases", SOURCE_ALIASES, skip_if_contains=".bash_aliases")
        if IS_MACOS or shutil.which("zsh"):
            self.ensure_block(HOME / ".zshrc", "aliases", SOURCE_ALIASES, skip_if_contains=".bash_aliases")
        self._configure_login_shell()

    def _configure_login_shell(self):
        """Login shells (macOS Terminal, Git Bash) read a profile instead of .bashrc.

        bash picks the first of .bash_profile, .bash_login, .profile that exists,
        so the block goes into whichever file bash will actually read.
        """
        for name in (".bash_profile", ".bash_login"):
            profile = HOME / name
            if profile.exists():
                self.ensure_block(profile, "bashrc", SOURCE_BASHRC, skip_if_contains=".bashrc")
                return
        self.ensure_block(HOME / ".profile", "bashrc", SOURCE_BASHRC, skip_if_contains=".bashrc")

    def ensure_block(self, path, name, lines, skip_if_contains=None):
        """Appends a marked block to path unless the marker or skip_if_contains is already present."""
        start = BLOCK_START.format(name=name)
        existing = self._read_text(path)
        if start in existing:
            self.log("ok", "{} already has block '{}'".format(path, name))
            return
        if skip_if_contains and skip_if_contains in existing:
            self.log("ok", "{} already references {}".format(path, skip_if_contains))
            return
        block = "\n".join([start] + lines + [BLOCK_END.format(name=name)])
        self.log("append", "{} block '{}'".format(path, name))
        if self.dry_run:
            return
        with open(str(path), "a", encoding="utf-8", newline="\n") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("\n" + block + "\n")

    @staticmethod
    def _read_text(path):
        """Returns the file content, or an empty string when it does not exist."""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ""


# -- virtual environment bootstrap ---------------------------------------------


def in_repo_venv():
    """True when the running interpreter is the one inside VENV_DIR."""
    if os.environ.get(VENV_GUARD):
        return True
    try:
        return Path(sys.prefix).resolve() == VENV_DIR.resolve()
    except OSError:
        return False


def create_venv():
    """Creates VENV_DIR, falling back to a pip-less venv where ensurepip is missing.

    Debian/Ubuntu ship ensurepip in a separate python3-venv package; without it
    the venv itself still works, only pip is absent.
    """
    import venv

    print("creating virtual environment: {}".format(VENV_DIR), flush=True)
    try:
        venv.create(str(VENV_DIR), with_pip=True, clear=True)
    except Exception as exc:
        print("  pip could not be bootstrapped ({}); creating the venv without pip".format(exc))
        print("  hint: on Debian/Ubuntu run: sudo apt install python3-venv")
        shutil.rmtree(str(VENV_DIR), ignore_errors=True)
        venv.create(str(VENV_DIR), with_pip=False, clear=True)


def requirements_listed():
    """True when requirements.txt names at least one package."""
    if not REQUIREMENTS.is_file():
        return False
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return True
    return False


def install_requirements():
    """Installs requirements.txt into the venv; a no-op when everything is already present."""
    print("installing requirements: {}".format(REQUIREMENTS), flush=True)
    cmd = [str(VENV_PYTHON), "-m", "pip", "install", "--quiet", "--requirement", str(REQUIREMENTS)]
    if subprocess.call(cmd) != 0:
        sys.exit("pip install failed; the venv may lack pip (see python3-venv hint above)")


def ensure_venv():
    """Creates .venv on first run and re-executes this script inside it."""
    if in_repo_venv():
        return
    if not VENV_PYTHON.exists():
        create_venv()
    if requirements_listed():
        install_requirements()
    env = dict(os.environ)
    env[VENV_GUARD] = "1"
    cmd = [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:]
    sys.stdout.flush()
    sys.exit(subprocess.call(cmd, env=env))


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--copy", action="store_true", help="copy files instead of symlinking them")
    parser.add_argument("--dry-run", action="store_true", help="show what would be done without changing anything")
    parser.add_argument("--no-venv", action="store_true", help="skip the .venv bootstrap and run with the current interpreter")
    args = parser.parse_args()

    if args.dry_run and not VENV_PYTHON.exists() and not args.no_venv:
        print("[dry-run] would create virtual environment: {}".format(VENV_DIR))
    elif not args.no_venv and not args.dry_run:
        ensure_venv()

    installer = Installer(copy=args.copy, dry_run=args.dry_run)
    print("repo:   {}\nhome:   {}\npython: {}\n".format(REPO_DIR, HOME, sys.executable))
    installer.install_all()
    installer.configure_shells()
    print("\ndone. Open a new terminal (or run: source ~/.bashrc) to pick up the changes.")


if __name__ == "__main__":
    main()
