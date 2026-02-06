# Timekpr - KDE Parental Control Configuration

A KDE System Settings module for configuring timekpr, a parental control utility that limits user access and usage time on Linux systems.

## Repository Structure

- **_timekpr/** - Main development repo (GitHub: simgunz/timekpr, branch: dev)
  - KDE configuration interface for timekpr
  - Components: backend daemon, KCM module, plasma applet, dataengine
  - Note: Contains nested git repo at `src/applet/package/.git` (should be cleaned up)

- **garbage/_timekprREM/** - Experimental sleep detection branch
  - Branch: sleepdetect
  - Work-in-progress features

## Status

Historical project (2011-2015). No longer actively developed.

Main branch (dev) is clean and pushed to GitHub.

## Links

- GitHub: https://github.com/simgunz/timekpr
- License: GPL-3.0
