import time
import os
from rich.console import Console

console = Console()


class Logger:
    def __init__(self, debug: bool, write_out_log=False, show_tm=True, log_path=""):
        self.debug = debug
        self.write_out_log = write_out_log
        self.show_tm = show_tm
        self._log_path = f"{os.path.split(__file__)[0]}/log" if log_path == "" else log_path

    def logger(self, msg, debug=False, warning=False, error=False):
        _tm = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}]" if self.show_tm else ""
        if error:
            self._printout(f"{_tm}[ERROR] {msg}", "red")
        elif warning:
            self._printout(f"{_tm}[WARNING] {msg}", "bright_yellow")
        elif debug and self.debug:
            self._printout(f"{_tm}[DEBUG] {msg}", "blue")
        elif not debug:
            self._printout(f"{_tm}[INFO] {msg}")

    def _printout(self, content, color="default"):
        console.print(content, style=color)
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
