# dotfiles

Terminal environment (WezTerm + shell aliases) shared across Linux, macOS and Windows.

## Layout

    home/            mirrors ~  (home/.wezterm.lua -> ~/.wezterm.lua, etc.)
    install.py       applies the repo to this machine; stdlib only, Python 3.6+
    requirements.txt Python packages for the tooling, installed into .venv/

## Fresh machine

1. Install [WezTerm](https://wezfurlong.org/wezterm/) and Python 3.
   On Windows also install [Git for Windows](https://git-scm.com/download/win)
   (provides Git Bash, which runs the aliases) or enable WSL.
2. Clone this repo, then run the installer:

       git clone <repo-url> ~/dotfiles
       python3 ~/dotfiles/install.py      # Windows: python ~\dotfiles\install.py

3. Open a new terminal.

`install.py` symlinks every file under `home/` into `~`, backs up anything it
replaces as `<name>.bak-<timestamp>`, and patches `.bashrc`, `.zshrc` and the
bash login profile so the aliases load everywhere. Re-running is safe.

Flags: `--dry-run` shows the plan without touching anything, `--copy` copies
instead of linking, `--no-venv` skips the virtual environment.

## Python environment

On first run `install.py` creates a virtual environment in `.venv/` (ignored
by git), installs `requirements.txt` into it and re-executes itself there.
Any Python dependency the tooling ever needs goes into `requirements.txt`,
never into the system interpreter. The installer itself is standard library
only, so the venv starts empty.

On Debian/Ubuntu a fresh machine may lack `ensurepip`; the installer then
creates the venv without pip and prints a hint (`sudo apt install python3-venv`).
Everything works without pip as long as `requirements.txt` lists no packages.

## Adding a file

Drop it under `home/` at the path it should have relative to `~`
(e.g. `home/.config/wezterm/colors/mine.toml`), then re-run `install.py`.

## Platform notes

- **Windows** refuses symlinks unless Developer Mode is on; the installer then
  copies. In that case edit the file in the repo and re-run `install.py`
  rather than editing the copy in `~`.
- **WSL** is a separate Linux home: clone and run the installer inside WSL too.
- **macOS** defaults to zsh; the aliases file is plain enough to work there and
  `.zshrc` is patched to load it.
- Line endings are forced to LF via `.gitattributes` so Git Bash can source
  the files even with `core.autocrlf=true`.

## Never commit secrets

Tokens and machine-specific paths stay in `~/.bashrc` (or a `~/.bashrc.local`),
not in this repo.
