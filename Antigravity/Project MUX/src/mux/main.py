"""Main executable entrypoint for MUX."""
import sys
from mux.cli.app import run

def main() -> None:
    sys.exit(run())

if __name__ == "__main__":
    main()
