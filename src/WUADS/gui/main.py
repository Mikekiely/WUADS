# src/wuads/main.py

import sys
import argparse
from pathlib import Path
from importlib import resources
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow
from ..aircraft import Aircraft  # Handles loading config internally

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        nargs="?",  # Makes it optional
        help="Path to input configuration .yml file"
    )
    args = parser.parse_args()

    if args.config:
        config_path = Path(args.config)
    else:
        try:
            # Works when installed as a package
            default_path = resources.files("WUADS.assets").joinpath("737-800.yml")
        except (ModuleNotFoundError, AttributeError):
            # Fallback for running from cloned repo
            default_path = Path(__file__).parent / "assets" / "737-800.yml"
        config_path = default_path

    aircraft = Aircraft(config_path)  # Pass path directly to Aircraft

    app = QApplication(sys.argv)
    window = MainWindow(aircraft=aircraft)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()