# Timekpr - KDE Parental Control Configuration

A KDE System Settings module for configuring timekpr, a parental control utility that limits user access and usage time on Linux systems.

## Features

- KDE Control Module (KCM) for system settings integration
- Backend daemon for time tracking and enforcement
- Plasma applet for desktop integration
- Data engine for real-time status updates

## Installation

### Dependencies

- gcc
- make
- cmake
- automoc4

### Install

```bash
sudo ./install.sh
```

After installation, you may need to restart Plasma:

```bash
kquitapp plasma-desktop
plasma-desktop
```

Or simply reboot your system.

### Uninstall

```bash
sudo ./uninstall.sh
```

To completely purge configuration:

```bash
sudo ./uninstall.sh purge
```

## Status

Historical project (2011-2015). No longer actively developed.

## Links

- GitHub: https://github.com/simgunz/timekpr
- License: GPL-3.0
