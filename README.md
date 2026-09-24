# dotfiles

Terminal environment (WezTerm + shell aliases) shared across Linux, macOS and Windows.

    home/             mirrors ~  (home/.wezterm.lua -> ~/.wezterm.lua, etc.)
    install.py        links home/ into ~ and wires up the shells; Python 3.6+, no deps
    requirements.txt  Python packages for the tooling, installed into .venv/

## Fresh machine

1. Install [WezTerm](https://wezfurlong.org/wezterm/) and Python 3.
   On Windows also install [Git for Windows](https://git-scm.com/download/win)
   (Git Bash runs the aliases) or enable WSL.
2. Clone and run:

       git clone <repo-url> ~/dotfiles
       python3 ~/dotfiles/install.py      # Windows: python ~\dotfiles\install.py

3. Open a new terminal.

The first run creates `.venv/` (git-ignored) and re-runs itself inside it.
Every file under `home/` is symlinked into `~`; anything already there is kept
as `<name>.bak`. `.bashrc`, `.zshrc` (where zsh exists) and the bash login
profile get one line each so the aliases load everywhere. Re-running is safe.

## Adding things

- New alias: edit `home/.bash_aliases` (symlinked to `~/.bash_aliases`).
- New dotfile: put it under `home/` at its path relative to `~`, re-run `install.py`.
- Python dependency for the tooling: add it to `requirements.txt`.

## Platform notes

- **Windows** refuses symlinks unless Developer Mode is on, so the installer
  copies instead. Edit files in the repo and re-run, not the copies in `~`.
- **WSL** has its own Linux home: clone and run the installer inside WSL too.
- **macOS** defaults to zsh; the aliases file works there unchanged.
- **Debian/Ubuntu** may need `sudo apt install python3-venv` before the first run.
- Line endings are forced to LF (`.gitattributes`) so Git Bash can source the files.

## Never commit secrets

Tokens and machine-specific paths stay in `~/.bashrc`, not in this repo.
