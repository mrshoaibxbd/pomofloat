import sys

from . import __version__


def main() -> int:
    if "--version" in sys.argv[1:]:
        print(f"pomofloat {__version__}")
        return 0

    from .app import main as app_main

    app_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
