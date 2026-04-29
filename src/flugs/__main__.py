"""CLI entry point for FLUGS.

``python -m flugs -c <config>`` runs the inversion pipeline.
"""

from .run import main


if __name__ == "__main__":
    main()
