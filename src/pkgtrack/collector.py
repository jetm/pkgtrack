from datetime import UTC, datetime, timedelta


def query_journal(since: datetime) -> list[str]:
    """Query journald for pkgtrack-collector.service entries.

    Args:
        since: Timezone-aware datetime to seek to.

    Returns:
        List of raw MESSAGE strings from matching journal entries.
    """
    try:
        from systemd import journal
    except ImportError:
        raise SystemExit("python-systemd is required. Install it with: sudo pacman -S python-systemd")

    reader = journal.Reader()
    reader.log_level(journal.LOG_INFO)
    reader.add_match(_SYSTEMD_UNIT="pkgtrack-collector.service")
    reader.seek_realtime(since)

    messages = []
    for entry in reader:
        msg = entry.get("MESSAGE", "")
        if msg:
            messages.append(msg)

    return messages


def parse_execsnoop_line(line: str) -> str | None:
    """Extract the executable path from a single execsnoop -T output line.

    execsnoop -T format: TIME PCOMM PID PPID RET ARGS
    The ARGS column contains the full command line; the first token is the executable path.

    Args:
        line: A single line of execsnoop output.

    Returns:
        The executable path (first token of ARGS), or None if the line should be skipped.
    """
    parts = line.split()
    # Need at least: TIME PCOMM PID PPID RET <one ARGS token>
    if len(parts) < 6:
        return None

    # Skip header line: "TIME PCOMM PID PPID RET ARGS"
    if parts[0] == "TIME" and parts[1] == "PCOMM":
        return None

    # ARGS starts at index 5; first token is the executable path
    executable = parts[5]

    # Only include absolute paths (package-managed binaries are always absolute)
    if not executable.startswith("/"):
        return None

    return executable


def collect_executed_paths(days: int = 30) -> set[str]:
    """Query the journal and return the set of unique executable paths executed.

    Args:
        days: Number of days to look back in the journal.

    Returns:
        Set of unique absolute executable paths seen in the collection window.
    """
    since = datetime.now(tz=UTC) - timedelta(days=days)
    messages = query_journal(since=since)

    paths: set[str] = set()
    for line in messages:
        path = parse_execsnoop_line(line)
        if path is not None:
            paths.add(path)

    return paths
