import time
from colorama import init
import os

init(autoreset=True)


class Style:
    DEFAULT = 0
    BOLD = 1
    ITALIC = 3
    UNDERLINE = 4
    ANTIWHITE = 7


class Color:
    DEFAULT = 39
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    PURPLE = 35
    CYAN = 36
    WHITE = 37
    LIGHTBLACK_EX = 90
    LIGHTRED_EX = 91
    LIGHTGREEN_EX = 92
    LIGHTYELLOW_EX = 93
    LIGHTBLUE_EX = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX = 96
    LIGHTWHITE_EX = 97


class BGColor:
    DEFAULT = 49
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    PURPLE = 45
    CYAN = 46
    WHITE = 47
    LIGHTBLACK_EX = 100
    LIGHTRED_EX = 101
    LIGHTGREEN_EX = 102
    LIGHTYELLOW_EX = 103
    LIGHTBLUE_EX = 104
    LIGHTMAGENTA_EX = 105
    LIGHTCYAN_EX = 106
    LIGHTWHITE_EX = 107


class Logger:
    def __init__(self, debug: bool, write_out_log=False, show_tm=True, log_path=""):
        self.debug = debug
        self.write_out_log = write_out_log
        self.show_tm = show_tm
        self._log_path = f"{os.path.split(__file__)[0]}/log" if log_path == "" else log_path

    def logger(self, msg, debug=False, warning=False, error=False):
        _tm = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}]" if self.show_tm else ""
        if error:
            self._printout(f"{_tm}[ERROR] {msg}", Color.RED)
        elif warning:
            self._printout(f"{_tm}[WARNING] {msg}", Color.LIGHTYELLOW_EX)
        elif debug and self.debug:
            self._printout(f"{_tm}[DEBUG] {msg}", Color.BLUE)
        elif not debug:
            self._printout(f"{_tm}[INFO] {msg}")

    def _printout(self, content, color=Color.DEFAULT, bgcolor=BGColor.DEFAULT, style=Style.DEFAULT):
        print("\033[{};{};{}m{}\033[0m".format(style, color, bgcolor, content))
        if self.write_out_log:
            self._write_log(content)

    def _write_log(self, content):
        _tm = time.strftime("%Y-%m-%d", time.localtime())
        try:
            with open(f"{self._log_path}/{_tm}.log", "a", encoding="utf8") as f:
                f.write(f"{content}\n")
        except FileNotFoundError:
            os.makedirs(f"{self._log_path}")


logger = Logger(False, show_tm=False)
