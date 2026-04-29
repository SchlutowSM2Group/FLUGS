"""Thin script wrapper around :mod:`flugs.run`.

Exists so that:

    python runs/run_flugs.py -c <config>

works equivalently to:

    python -m flugs -c <config>
"""

from flugs.run import main

if __name__ == "__main__":
    main()
