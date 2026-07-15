import sys

from controller.main_controller import MainController


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    MainController().run()


if __name__ == "__main__":
    main()
