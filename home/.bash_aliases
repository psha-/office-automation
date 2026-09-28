# Shell aliases shared across machines; sourced by bash and zsh.
# Managed by ~/dotfiles: edit the copy in the repo and re-run install.py.

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias clo='claude --dangerously-skip-permissions'

# Desktop notification for long running commands, e.g.:  sleep 10; alert
# Defined only where notify-send exists (Linux desktops).
if command -v notify-send >/dev/null 2>&1; then
    alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'
fi
