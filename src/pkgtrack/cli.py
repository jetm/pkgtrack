import subprocess
import sys

import click
from rich.console import Console

from pkgtrack.collector import collect_executed_paths
from pkgtrack.packages import build_reverse_index, get_package_sizes
from pkgtrack.report import print_report

console = Console()


@click.group()
@click.version_option(package_name="pkgtrack")
def cli():
    """Track which Arch Linux packages you actually use."""


@cli.command()
@click.option("--days", default=30, show_default=True, help="Number of days to look back in the journal.")
def analyze(days: int):
    """Analyze package usage and report unused packages."""
    # Preflight: check journal read permissions
    try:
        from systemd import journal
    except ImportError:
        console.print("[red]Error:[/red] python-systemd is required. Install with: sudo pacman -S python-systemd")
        sys.exit(1)

    try:
        reader = journal.Reader()
        reader.close()
    except PermissionError:
        console.print("[red]Error:[/red] Cannot read journal. Add your user to the 'systemd-journal' group.")
        sys.exit(1)

    # Preflight: check if collector service is active
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", "pkgtrack-collector.service"],
        capture_output=True,
    )
    if result.returncode != 0:
        console.print(
            "[yellow]Warning:[/yellow] pkgtrack-collector.service is not running. No new executions are being recorded."
        )

    # Query journal for executed paths
    console.print(f"Querying journal for the last {days} days...")
    executed_paths = collect_executed_paths(days=days)

    if not executed_paths:
        console.print("[yellow]Warning:[/yellow] No execution data found in the journal for this time window.")
        console.print("Make sure pkgtrack-collector.service has been running.")
        return

    console.print(f"Found {len(executed_paths)} unique executed paths.")

    # Build reverse index: path -> package
    console.print("Building package index...")
    reverse_index = build_reverse_index()
    all_packages_with_binaries = set(reverse_index.values())

    # Find which packages had at least one binary executed
    used_packages: set[str] = set()
    for path in executed_paths:
        pkg = reverse_index.get(path)
        if pkg:
            used_packages.add(pkg)

    # Compute unused = all explicit packages with binaries minus used
    unused_packages = all_packages_with_binaries - used_packages

    total = len(all_packages_with_binaries)
    console.print(f"{total} explicit packages with binaries, {len(used_packages)} used, {len(unused_packages)} unused.")

    # Build report data: (package_name, installed_size)
    sizes = get_package_sizes(unused_packages)
    report_data = [(pkg, sizes.get(pkg, 0)) for pkg in unused_packages]

    print_report(report_data)
