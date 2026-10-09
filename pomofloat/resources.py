"""Locate installed and source-tree application resources."""
from pathlib import Path


def logo_path() -> Path | None:
    candidates = (
        Path(__file__).resolve().parent.parent / "data" / "pomofloat.png",
        Path("/usr/share/pixmaps/pomofloat.png"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None
