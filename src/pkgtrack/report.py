from rich.console import Console
from rich.table import Table

console = Console()


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024**3:
        return f"{size_bytes / 1024**3:.1f} GiB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / 1024**2:.1f} MiB"
    return f"{size_bytes / 1024:.1f} KiB"


def print_report(packages: list[tuple[str, int]]) -> None:
    """Display a rich table of unused packages sorted by size descending."""
    if not packages:
        console.print("[green]No unused packages found.[/green]")
        return

    sorted_packages = sorted(packages, key=lambda p: p[1], reverse=True)

    table = Table(title="Unused Packages", show_footer=True)
    table.add_column("Package Name", footer=f"{len(sorted_packages)} packages")
    table.add_column("Installed Size", justify="right", footer=_format_size(sum(s for _, s in sorted_packages)))

    for name, size in sorted_packages:
        table.add_row(name, _format_size(size))

    console.print(table)
