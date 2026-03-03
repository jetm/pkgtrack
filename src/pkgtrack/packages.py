import re
import subprocess

_SIZE_MULTIPLIERS = {"KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}


def build_reverse_index() -> dict[str, str]:
    """Build a path -> package_name mapping for all /usr/bin/ files from explicitly-installed packages.

    Runs `pacman -Qqe` to get explicit packages, then `pacman -Ql <pkg1> <pkg2> ...` once
    for all packages to retrieve their file lists in a single subprocess call.
    Returns a dict mapping each /usr/bin/ path to its owning package name.
    """
    result = subprocess.run(["pacman", "-Qqe"], capture_output=True, text=True, check=True)
    packages = result.stdout.splitlines()

    if not packages:
        return {}

    result = subprocess.run(["pacman", "-Ql"] + packages, capture_output=True, text=True, check=True)

    index: dict[str, str] = {}
    for line in result.stdout.splitlines():
        # Each line is: "<pkg_name> <path>"
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        pkg_name, path = parts
        if path.startswith("/usr/bin/") and not path.endswith("/"):
            index[path] = pkg_name

    return index


def get_package_sizes(packages: set[str]) -> dict[str, int]:
    """Return installed sizes in bytes for all given packages in a single pacman call."""
    if not packages:
        return {}

    result = subprocess.run(["pacman", "-Qi"] + sorted(packages), capture_output=True, text=True, check=True)

    sizes: dict[str, int] = {}
    current_pkg = None
    for line in result.stdout.splitlines():
        if line.startswith("Name"):
            match = re.search(r":\s+(\S+)", line)
            if match:
                current_pkg = match.group(1)
        elif line.startswith("Installed Size") and current_pkg:
            match = re.search(r":\s+([\d.]+)\s+(KiB|MiB|GiB)", line)
            if match:
                value = float(match.group(1))
                sizes[current_pkg] = int(value * _SIZE_MULTIPLIERS[match.group(2)])
            current_pkg = None

    return sizes
