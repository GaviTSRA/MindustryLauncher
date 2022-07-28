import http.client as httplib
from time import time

def internet_available():
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()

class LogLevel:
    DEBUG = (0, "Debug")
    INFO = (1, "Info")
    WARN = (2, "Warn")
    ERROR = (3, "Error")

class Logger:
    def __init__(self, source, lvl, file_name) -> None:
        self.source = source
        self.lvl = lvl
        self.file_name = file_name

    def log(self, lvl, text):
        with open(self.file_name, "a") as fi:
            fi.write(f"[{lvl[1]}] [{self.source}] {text}\n")

    def debug(self, text):
        if self.lvl[0] <= LogLevel.DEBUG[0]:
            self.log(LogLevel.DEBUG, text)

    def info(self, text):
        if self.lvl[0] <= LogLevel.INFO[0]:
            self.log(LogLevel.INFO, text)

    def warn(self, text):
        if self.lvl[0] <= LogLevel.WARN[0]:
            self.log(LogLevel.WARN, text)

    def error(self, text):
        if self.lvl[0] <= LogLevel.ERROR[0]:
            self.log(LogLevel.ERROR, text)