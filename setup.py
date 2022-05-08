# -*- coding: utf-8 -*-
import sys

from cx_Freeze import Executable, setup

from version import version

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': ['atexit'],
        'packages': ['queue', 'organizador'],
        'excludes': [],
        'include_msvcr': True,
        'optimize': 2
    }
}

executables = [
    Executable('new_main_ui.py', base=base,
               target_name='Organizador de Series.exe', icon='icon.ico')
]

setup(name='Organizador',
      version=version,
      description='Organizador de Series',
      options=options,
      executables=executables
      )
