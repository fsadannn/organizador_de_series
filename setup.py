# -*- coding: utf-8 -*-
import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': ['atexit', 'utils', 'mvrename', 'falta', 'appicon',
                      'stopwords', 'parser_serie', 'ftp_manager'],
        'optimize': 2
    }
}

executables = [
    Executable('mangas_ui.py', base=base,
               targetName='Organizador de Series.exe', icon='icon.ico')
]

setup(name='Organizador',
      version='3.5',
      description='Organizador de Series',
      options=options,
      executables=executables
      )
