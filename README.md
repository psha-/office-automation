# dotfiles

Terminal environment (WezTerm + shell aliases) shared across Linux, macOS and Windows.

    home/             mirrors ~  (home/.wezterm.lua -> ~/.wezterm.lua, etc.)
    install.py        links home/ into ~ and wires up the shells; Python 3.6+, no deps

## Fresh machine

1. Install [WezTerm](https://wezfurlong.org/wezterm/) and Python 3.
   On Windows also install [Git for Windows](https://git-scm.com/download/win)
   (Git Bash runs the aliases) or enable WSL.
2. Clone and run:

       git clone <repo-url> ~/dotfiles
       python3 ~/dotfiles/install.py      # Windows: python ~\dotfiles\install.py

## Adding things

- New alias: edit `home/.bash_aliases` (symlinked to `~/.bash_aliases`).
- New dotfile: put it under `home/` at its path relative to `~`, re-run `install.py`.

## Platform notes

- **Windows** refuses symlinks unless Developer Mode is on, so the installer
  copies instead. Edit files in the repo and re-run, not the copies in `~`.
- **WSL** has its own Linux home: clone and run the installer inside WSL too.
- **macOS** defaults to zsh; the aliases file works there unchanged.
- Line endings are forced to LF (`.gitattributes`) so Git Bash can source the files.

## Never commit secrets

Tokens and machine-specific paths stay in `~/.bashrc`, not in this repo.
