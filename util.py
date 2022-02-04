import urllib.parse
from datetime import datetime as dt
from random import randint as rd


def get_time() -> str:
    now = dt.now()
    h, m, s = now.hour, now.minute, now.second
    return '%s%s%s' % ('{:0>2d}'.format(h), '{:0>2d}'.format(m), '{:0>2d}'.format(s))


def get_date() -> str:
    now = dt.now()
    year, month, day = now.year, now.month, now.day
    return '%s%s%s' % (str(year), '{:0>2d}'.format(month), '{:0>2d}'.format(day))


def search(keys: str) -> str:
    keys = urllib.parse.quote(keys)
    s = ''
    s += 'm.youdao.com/dict?q=%s\n\n' % keys
    s += 'iciba.com/word?w=%s\n\n' % keys
    s += 'bing.com/dict/search?q=%s\n\n' % keys
    s += 'bing.com/search?q=%s' % keys
    return s


def generate_verification_code() -> str:
    code = s = ''
    for i in range(ord('a'), ord('z') + 1):
        s += chr(i)
    for i in range(ord('A'), ord('Z') + 1):
        s += chr(i)
    for i in range(10):
        s += str(i)
    for i in range(10):
        code += s[rd(0, len(s) - 1)]
    return code
