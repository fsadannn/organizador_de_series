import datetime
from math import floor
from typing import Union

_current_year = datetime.date.today().year
_year_gap = 100


def is_valid_year(txt: str) -> bool:
    txt = txt.strip()
    try:
        data = int(txt)

        if 1920 <= data <= _current_year + _year_gap:
            return True

        return False
    except ValueError:
        return False


def number_to_str(number: Union[float, int]) -> str:
    has_fraction = abs(number - floor(number)) > 1e-9

    if has_fraction:
        return str(number)

    return str(int(number))


class Stack:  # pragma: no cover
    __slots__ = tuple(['_stack', '_id'])

    def __init__(self, idd: str = ''):
        self._stack: list = []
        self._id = idd

    def __len__(self):
        return len(self._stack)

    @property
    def id(self) -> str:
        return self._id

    @property
    def stack(self) -> list:
        return self._stack

    @property
    def empty(self) -> bool:
        return len(self._stack) == 0

    def isempty(self) -> bool:
        return len(self._stack) == 0

    def top(self):
        if len(self._stack) == 0:
            raise IndexError('top from empty Stack')
        return self._stack[-1]

    def push(self, value):
        self._stack.append(value)

    def pop(self):
        if len(self._stack) == 0:
            raise IndexError('pop from empty Stack')
        val = self._stack.pop()
        return val

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}< id="{self.id}" >'
