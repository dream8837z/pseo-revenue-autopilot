"""Allow `python3 -m pseo_engine` execution."""

import sys

from pseo_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
