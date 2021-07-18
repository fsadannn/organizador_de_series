# -*- coding: utf-8 -*-
import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': ['atexit', 'utils', 'move_rename', 'falta', 'appicon',
                     'stopwords', 'parser_serie', 'sync'],
        'include_files': ['options.json'],
        'packages': ['pkginfo', 'pkg_resources', 'babelfish', 'queue'],
        'include_msvcr': True,
        'optimize': 2
    }
}

executables = [
    Executable('main_ui.py', base=base,
               target_name='Organizador de Series.exe', icon='icon.ico')
]

setup(name='Organizador',
      version='4.12.2',
      description='Organizador de Series',
      options=options,
      executables=executables
      )
