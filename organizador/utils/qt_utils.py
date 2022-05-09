from enum import Enum, unique
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal


class Logger(QObject):
    __slots__ = ('__name', '__signal')

    def __init__(self, name: str, signal: pyqtSignal):
        self.__name: str = name
        self.__signal: pyqtSignal = signal

    def emit(self, txt: str, num: int):
        self.__signal.emit(self.__name, txt, num)

    @property
    def signal(self) -> pyqtSignal:
        return self.__signal


def reconnect(signal: pyqtSignal, newhandler: Optional[Callable[..., Optional[str]]] = None, oldhandler: Optional[Callable[..., Optional[str]]] = None):
    while True:
        try:
            if oldhandler is not None:
                signal.disconnect(oldhandler)
            else:
                signal.disconnect()
        except TypeError:
            break
    if newhandler is not None:
        signal.connect(newhandler)


@unique
class LogLevel(Enum):
    NAME = 0
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    DEBUG = 4


LOG_COLORS = dict([(LogLevel.INFORMATION.value, "green"),
                   (LogLevel.WARNING.value, "orange"),
                   (LogLevel.ERROR.value, "red"),
                   (LogLevel.DEBUG.value, "blue"),
                   (LogLevel.NAME.value, "black")])


def logcolor(txt, level: int) -> str:
    return f'<font color="{LOG_COLORS[level]}">{txt}</font>'


def logsize(txt, size) -> str:
    return f'<h{size}>{txt}</h{size}>'
