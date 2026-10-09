from abc import ABC, abstractmethod
from enum import IntEnum


class LogLevel(IntEnum):
    INFO = 1
    WARNING = 2
    ERROR = 3

class LogHandler(ABC):
    def __init__(self, next_handler=None):
        self.next_handler = next_handler

    def set_next(self, handler):
        self.next_handler = handler
        return handler

    @abstractmethod
    def handle(self, level, message):
        if self.next_handler:
            return self.next_handler.handle(level, message)
        return None


class InfoHandler(LogHandler):
    def handle(self, level, message):
        if level == LogLevel.INFO:
            print(f"[INFO] {message}")
            return None

        return super().handle(level, message)

class WarningHandler(LogHandler):
    def handle(self, level, message):
        if level == LogLevel.WARNING:
            print(f"[WARNING] {message}")
            return None

        return super().handle(level, message)


class ErrorHandler(LogHandler):
    def handle(self, level, message):
        if level == LogLevel.ERROR:
            print(f"[ERROR] {message}")
            return None

        return super().handle(level, message)


info = InfoHandler()
warning = WarningHandler()
error = ErrorHandler()

info.set_next(warning).set_next(error)
info.handle(LogLevel.ERROR, "Database is down")
