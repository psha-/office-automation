-- WezTerm configuration shared across Linux, macOS and Windows.
-- WezTerm reads ~/.wezterm.lua on every platform, so one file covers all.
local wezterm = require("wezterm")
local config = wezterm.config_builder()

--- Returns true when the file at path can be opened for reading.
local function file_exists(path)
  local f = io.open(path, "r")
  if f then
    f:close()
    return true
  end
  return false
end

--- Returns the first path in the list that exists, or nil.
local function first_existing(paths)
  for _, p in ipairs(paths) do
    if file_exists(p) then
      return p
    end
  end
  return nil
end

-- Appearance
config.font_size = 11.0
config.hide_tab_bar_if_only_one_tab = true

-- Windows ships without bash, so the aliases in ~/.bash_aliases need
-- Git Bash or WSL. Prefer Git Bash, fall back to WSL, else keep the default.
if wezterm.target_triple:find("windows") then
  local candidates = {
    "C:\\Program Files\\Git\\bin\\bash.exe",
    "C:\\Program Files (x86)\\Git\\bin\\bash.exe",
  }
  local local_app_data = os.getenv("LOCALAPPDATA")
  if local_app_data then
    table.insert(candidates, local_app_data .. "\\Programs\\Git\\bin\\bash.exe")
  end
  local system_root = os.getenv("SystemRoot") or "C:\\Windows"

  local git_bash = first_existing(candidates)
  if git_bash then
    config.default_prog = { git_bash, "-l" }
  elseif file_exists(system_root .. "\\System32\\wsl.exe") then
    config.default_prog = { "wsl.exe", "~" }
  end
end

return config
