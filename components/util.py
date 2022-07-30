import socket

def internet_available(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

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