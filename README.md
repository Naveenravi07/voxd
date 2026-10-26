# voxd

Voice dictation daemon for Linux. Press keybind, talk, press again. Text goes to clipboard.

## Install

```bash
pip install voxd
```

Dependencies:
```bash
# X11 (dwm, i3, bspwm, etc)
sudo pacman -S ffmpeg xclip

# Wayland (hyprland, sway, etc)
sudo pacman -S ffmpeg wl-clipboard
```

## Setup

Set your Sarvam AI API key:
```bash
voxd config set api_key YOUR_KEY
```

Optional - set language:
```bash
voxd config set language hi-IN  # Hindi
voxd config set language en-IN  # English (default)
```

## Start daemon

Add to your startup:

**dwm/i3/bspwm** - `~/.xinitrc`:
```bash
voxd-daemon &
```

**hyprland** - `~/.config/hypr/hyprland.conf`:
```ini
exec-once = voxd-daemon
```


## Keybind

**dwm** - `config.h`:
```c
{ MODKEY, XK_semicolon, spawn, SHCMD("voxd toggle --autostart") },
```


**hyprland** - `hyprland.conf`:
```ini
bind = SUPER, semicolon, exec, voxd toggle --autostart
```



## Usage

Press keybind → talk → press keybind → paste (Ctrl+V)

Terminal:
```bash
voxd toggle             # Start/stop recording
voxd toggle --autostart # Start daemon if needed, then toggle
voxd status             # Check if recording
voxd logs               # Show recent daemon logs
voxd logs -f            # Follow daemon logs
voxd logs --path        # Print daemon log path
voxd quit               # Kill daemon
```

## Config

```bash
voxd config list              # Show all settings
voxd config set key value     # Change setting
voxd config get key           # Get value
```

Settings:
- `api_key` - Sarvam AI key (required)
- `language` - Language code (default: en-IN)
- `model` - STT model (default: saaras:v3)

Config stored at `~/.config/voxd/config.json`

## Advanced

**WM-specific commands** (if auto-detect fails):
```bash
voxd-x11 toggle      # Force X11 mode
voxd-wayland toggle  # Force Wayland mode
```


## Troubleshooting

**Daemon not running:**
```bash
voxd toggle --autostart
voxd status
voxd logs
```

If `voxd toggle` says `daemon-not-running`, either start `voxd-daemon` from your WM/session startup or use `voxd toggle --autostart` in the keybind.

**No clipboard:**
```bash
# Install clipboard tool
sudo pacman -S xclip          # X11
sudo pacman -S wl-clipboard   # Wayland
```

**Wrong language:**
```bash
voxd config set language hi-IN
voxd quit && voxd-daemon &

```
