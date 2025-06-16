import sys
import rich
from core.app import app_factory

rich.print("The author of this system is https://github.com/Mova801\n")


def main() -> None:
    app = app_factory()
    app.start()


if __name__ == "__main__":
    main()
