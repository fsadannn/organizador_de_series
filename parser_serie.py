from __future__ import annotations
import re
import os
import sys
from typing import List
from stopwords import stopwords

if hasattr(sys, 'frozen'):
    MODULE = os.path.dirname(sys.executable)
else:
    try:
        MODULE = os.path.dirname(os.path.realpath(__file__))
    except:
        MODULE = ""

tv = re.compile('[^a-zA-Z0-9ñÑ][tT][vV][^a-zA-Z0-9ñÑ]')
normsp = re.compile('  +')
daysstr = ['lunes', 'martes', 'mi[eé]rcoles', 'jueves', 'viernes', 's[áa]bado', 'domingo',
           'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
days = re.compile('|'.join(daysstr), re.I)
dates = re.compile(
    '[0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4}|[0-9]{2,4}[/-][0-9]{1,2}[/-][0-9]{1,2}')
resolution = re.compile(
    '1080p|720p|480p|1920 *?[xX] *?1080|1280 *?[xX] *?720|720 *?[xX] *?480')
codec = re.compile('[Xx]264|[xX]265')
garbage = re.compile('\{ *\}|\( *\)|\[ *\]')

tokens_str = '[a-zA-Z0-9!ñÑ\']+|\-|'
tokens_str += '|'.join(['\{', '\(', '\['])
tokens_str += '|' + '|'.join(['\}', '\)', '\]'])
tokens = re.compile(tokens_str)
captemp = re.compile('([0-9]{1,3})[xX]([0-9]{1,4})', re.I)
seasonepi = re.compile('[Ss]([0-9]{1,3})[Ee]([0-9]{1,4})', re.I)
epi = re.compile(
    'chapters?$|episodes?$|episodios?$|cap[ií]tulos?$|caps?$', re.I)
epin = re.compile(
    'chapters?[0-9]+|episodes?[0-9]+|episodios?[0-9]+|cap[ií]tulos?[0-9]+|caps?[0-9]+', re.I)
upperm = re.compile('[A-Z].*?[A-Z]')
ordinal = re.compile(
    '1st|2nd|3rd|[1-9][0-9?]th|1ro|2do|3ro|[4-6]to|7mo|8vo|9no', re.I)

grouping = set(['{', '(', '[', '}', ')', ']'])
gopener = ['{', '(', '[']
gcloser = ['}', ')', ']']
grouping_d = {i: j for i, j in list(
    zip(gopener, gcloser)) + list(zip(gcloser, gopener))}
gopener = set(gopener)
gcloser = set(gcloser)
letn = re.compile('[0-9][a-z]', re.I)

keep = set(['kun', 'sama', 'chan', 'kai', 'senpai', 'man'])


def is_valid_year(txt: str) -> bool:
    txt = txt.strip()
    try:
        data = int(txt)
        if 1920 <= data <= 2030:
            return True
        return False
    except:
        return False


def transform(txt):
    res = []
    for n, i in enumerate(txt.split()):
        if i.lower() in stopwords and n != 0:
            res.append(i.lower())
        elif i == " ":
            continue
        elif len(i) == 2 and letn.search(i) and not ordinal.search(i):
            res.append(i[0] + i[1].upper())
        elif len(i) < 3 or upperm.search(i):
            res.append(i)
        elif len(i) == 1:
            res.append(i.lower())
        else:
            res.append(i[0].upper() + i[1:].lower())
    return ' '.join(res).strip()


def clean(txt: str):
    txt = txt.replace('?', '\?')
    txt = txt.replace('+', '\+')
    txt = txt.replace('.', '\.')
    txt = tv.sub(' ', txt)
    txt = days.sub('', txt)
    txt = dates.sub('', txt)
    txt = resolution.sub('', txt)
    txt = codec.sub('', txt)
    txt = garbage.sub('', txt)
    txt = normsp.sub(' ', txt)
    return txt.strip()


class Stack:  # pragma: no cover
    __slots__ = tuple(['_stack'])

    def __init__(self):
        self._stack: List[Token] = []

    def __len__(self):
        return len(self._stack)

    @property
    def stack(self) -> List[Token]:
        return self._stack

    @property
    def empty(self) -> bool:
        return len(self._stack) == 0

    def isempty(self) -> bool:
        return len(self._stack) == 0

    def top(self) -> Token:
        if len(self._stack) == 0:
            raise IndexError('top from empty Stack')
        return self._stack[-1]

    def push(self, value: Token):
        self._stack.append(value)

    def pop(self) -> Token:
        if len(self._stack) == 0:
            raise IndexError('pop from empty Stack')
        val = self._stack.pop()
        return val

    def __str__(self) -> str:
        return ' '.join(
            list(map(lambda x: str(x.value), self._stack))
        )


class Token:
    __slots__ = ('_value', '_is_group', '_is_opener', '_is_closer')

    def __init__(self, value):
        self._value = value
        self._is_group: bool = value in grouping
        self._is_opener: bool = value in gopener
        self._is_closer: bool = value in gcloser

    @property
    def is_grouping_token(self) -> bool:
        return self._is_group

    @property
    def is_opener_token(self) -> bool:
        return self._is_opener

    @property
    def is_closer_token(self) -> bool:
        return self._is_closer

    @property
    def value(self):
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def search(self, compiled_exp):
        return compiled_exp.search(self._value)

    def sub(self, compiled_exp, replace_str: str, count: int = 0):
        return compiled_exp.sub(replace_str, self._value, count)


class Group:
    __slots__ = ('_opener', '_closer', '_tokens')

    def __init__(self, opener):
        if not isinstance(opener, Token):
            opener = Token(opener)
        self._opener: Token = opener
        self._closer: Token = Token(grouping_d[opener.value])
        self._tokens: List[Token] = []

    @property
    def opener(self) -> Token:
        return self._opener

    @property
    def closer(self) -> Token:
        return self._closer

    @property
    def tokens(self) -> List[Token]:
        return self._tokens

    def __str__(self) -> str:
        return ' '.join([str(self._opener.value)]
                        + list(map(lambda x: str(x.value), self._tokens))
                        + [str(self._closer.value)])

    def append(self, value):
        if not isinstance(value, Token):
            value = Token(value)
        self._tokens.append(value)


def tokenize(txt) -> List[Token | Group]:
    toks: List[Token | Group] = []
    stack = Stack()
    for i in map(lambda x: x.group().strip(), tokens.finditer(txt)):
        tok = Token(i)
        if tok.is_grouping_token:
            if tok.is_opener_token:
                gp = Group(tok)
                stack.push(gp)
            else:
                gp = stack.pop()
                toks.append(gp)
        else:
            if stack.empty:
                toks.append(tok)
            else:
                gp = stack.top()
                gp.append(tok)

    if len(toks) == 1 and isinstance(toks[0], Group):
        toks = toks[0].tokens
    return toks


class Processor:
    __slots__ = ('_capcandidate', '_check', '_temp', '_name', '_cap',
                 '_check_cap', '_name_episode', '_temp_cap',
                 '_tokens', '_groups', '_candidate', '_season')

    def __init__(self):
        self._capcandidate = []
        self._check: bool = False
        self._name: Stack = Stack()
        self._name_episode: Stack = Stack()
        self._cap = None
        self._temp = None
        self._temp_cap = None
        self._check_cap: bool = False
        self._tokens: List[Token] = []
        self._groups: List[Group] = []
        self._candidate: List[List[Token, float, int]] = []
        self._season = None

    def _is_cap(self, token: Token) -> bool:
        if self._cap is not None:
            return False
        using = self._name if self._cap is None else self._name_episode

        if token.search(epin):
            self._check_cap = False
            ff = token.search(re.compile('[0-9]{1,4}'))
            self._cap = int(ff.group())
            return True

        if token.search(epi):
            # this flag is used to check the next token for chapter|episode number
            self._check_cap = True
            self._temp_cap = token
            return True

        if token.search(captemp):
            self._check_cap = False
            r = token.search(captemp)
            self._cap = int(r.groups()[1])
            self._season = int(r.groups()[0])
            return True

        if token.search(seasonepi):
            self._check_cap = False
            r = token.search(seasonepi)
            self._cap = int(r.groups()[1])
            self._season = int(r.groups()[0])
            return True

        if self._check_cap:
            self._check_cap = False
            ff = token.search(re.compile('[0-9]{1,4}'))

            if ff is not None:
                self._cap = int(ff.group())
                self._temp_cap = None
                return True

            using.push(self._temp_cap)
            self._temp_cap = None
            return False

        if token.search(re.compile('[0-9]{1,3}')) and not token.search(ordinal):
            candidate = (token,
                         int(bool(token.search(re.compile('[A-Za-z]+'))))
                         - int(bool(token.search(captemp)))
                         + 1 / len(self._tokens),
                         len(self._tokens)
                         )
            self._candidate.append(candidate)

    def _append(self, token: Token):
        using = self._name if self._cap is None else self._name_episode

        if token.value == '-':
            try:
                self._temp = token
            except:
                return
            self._check = True
            return

        if self._is_cap(token):
            return

        if self._check:
            if token.value in keep or \
                    (token.search(upperm) and using.top().search(upperm)):
                before = str(using.pop())
                sep = str(self._temp)
                after = str(token)
                newtok = Token(before + sep + after)
                using.push(newtok)
            else:
                using.push(token)
            self._temp = None
            self._check = False
            return

        using.push(token)

    def process(self, tokens: List[Token | Group]):
        for tok in tokens:
            if isinstance(tok, Group):
                self._groups.append(tok)
            else:
                self._tokens.append(tok)
                self._append(tok)

        # TODO: procees group using Processor

        if self._cap is None:
            if len(self._candidate) == 0:
                return

            if len(self._candidate) == 1:
                self._cap = int(self._candidate[0][0].search(
                    re.compile('[0-9]{1,4}')).group())
                return

            sorted_candidate = list(
                sorted(self._candidate, key=lambda x: x[1]))
            self._cap = int(sorted_candidate[0][0].search(
                re.compile('[0-9]{1,4}')).group())

    @property
    def data(self):
        return {
            'name': transform(str(self._name)),
            'nameep': transform(str(self._name_episode)),
            'cap': self._cap,
            'season': self._season
        }


def rename_serie(txt: str):
    cc = clean(txt)
    toks = tokenize(cc)
    p = Processor()
    p.process(toks)
    data = p.data
    if data['cap'] is None:
        cap = ''
        print(txt, data)
    else:
        cap = f"{data['season']}X{'0'*int(data['cap']<10)}{data['cap']}" if data['season'] else f"{'0'*int(data['cap']<10)}{data['cap']}"
    nameep = data['nameep'] if data['nameep'] else ''
    return data['name'], cap, nameep
