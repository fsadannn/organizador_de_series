# -*- coding: utf-8 -*-
import sys

from cx_Freeze import Executable, setup

from version import version

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': ['atexit', 'utils', 'move_rename', 'falta', 'appicon',
                     'stopwords', 'parser_serie', 'sync'],
        'include_files': ['options.json'],
        'packages': ['babelfish', 'queue', 'series_renamer'],
        'include_msvcr': True,
        'optimize': 2
    }
}

executables = [
    Executable('main_ui.py', base=base,
               target_name='Organizador de Series.exe', icon='icon.ico')
]

setup(name='Organizador',
      version=version,
      description='Organizador de Series',
      options=options,
      executables=executables
      )
