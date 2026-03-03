# pkgtrack

Track which Arch Linux packages you actually use via eBPF execution tracing.

## How It Works

A systemd service runs `execsnoop` (from `bcc-libbpf-tools`) continuously, tracing every `execve()` call and logging to journald. When you run `pkgtrack analyze`, it queries the journal for the past N days, cross-references the executed paths with pacman's package database, and identifies explicitly-installed packages whose binaries were never executed. Results are shown in a table sorted by installed size.

## Install

```
yay -S pkgtrack
```

## Setup

Enable the collector service (must be running to gather data):

```
sudo systemctl enable --now pkgtrack-collector.service
```

Wait at least a few days before analyzing so the journal has representative data.

## Usage

```
pkgtrack analyze
```

Look back further:

```
pkgtrack analyze --days 60
```

The `--days` flag defaults to 30.

## Requirements

- Arch Linux
- `bcc-libbpf-tools` (provides `execsnoop`)
- `python-systemd`

Your user must be able to read the systemd journal. If you see a permission error, add yourself to the `systemd-journal` group:

```
sudo usermod -aG systemd-journal $USER
```

## License

MIT
