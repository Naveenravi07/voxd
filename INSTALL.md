# Installation Guide

## Quick Install

```bash
pip install voxd
```

The commands are now globally available:
- `voxd` - main CLI
- `voxd-daemon` - background daemon
- `voxd-x11` - force X11 output mode
- `voxd-wayland` - force Wayland output mode

## Initial Setup

### 1. Set your API key

```bash
voxd config set api_key YOUR_SARVAM_API_KEY
```

### 2. (Optional) Configure language

```bash
# For Hindi
voxd config set language hi-IN

# For English (default)
voxd config set language en-IN
```

### 3. (Optional) Set model

```bash
voxd config set model saaras:v3
```

### 4. View your config

```bash
voxd config list
```

Config is stored in `~/.config/voxd/config.json`

## System Dependencies

Install these based on your setup:

```bash
# For X11 (dwm, i3, etc)
sudo pacman -S ffmpeg xclip

# For Wayland (hyprland, sway, etc)
sudo pacman -S ffmpeg wl-clipboard
```

## Start Daemon at Boot

### dwm / X11

Add to `~/.xinitrc` (before `exec dwm`):

```bash
voxd-daemon &
```

### hyprland / Wayland

Add to `~/.config/hypr/hyprland.conf`:

```ini
exec-once = voxd-daemon
```

## Setup Keybind

Use the plain `voxd toggle --autostart` command for normal setups. It auto-detects X11 or Wayland from your session environment.

### dwm

Edit your `config.h`:

```c
{ MODKEY, XK_semicolon, spawn, SHCMD("voxd toggle --autostart") },
```

Recompile: `sudo make clean install`

### hyprland

Add to `~/.config/hypr/hyprland.conf`:

```ini
bind = SUPER, semicolon, exec, voxd toggle --autostart
```

Reload: `hyprctl reload`

If auto-detection fails, use the backend-specific wrappers:

```bash
voxd-x11 toggle      # Force X11 mode
voxd-wayland toggle  # Force Wayland mode
```

## Usage

Press your keybind once to start recording, press again to stop. The transcribed text is copied to your clipboard - just paste with Ctrl+V!

You can also use the terminal:

```bash
# Toggle recording
voxd toggle --autostart

# Check status
voxd status

# Show recent daemon logs
voxd logs

# Follow daemon logs
voxd logs -f

# Stop daemon
voxd quit
```

## Troubleshooting

### Daemon not starting

Check if it's running:
```bash
ps aux | grep voxd-daemon
```

Check logs:
```bash
voxd logs
```

### API key not working

Make sure it's set:
```bash
voxd config get api_key
```

### No clipboard support

Install clipboard tools:
```bash
# X11
sudo pacman -S xclip

# Wayland
sudo pacman -S wl-clipboard
```
