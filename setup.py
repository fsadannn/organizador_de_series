# -*- coding: utf-8 -*-
import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit'
    }
}

executables = [
    Executable('mangas_ui.pyw', base=base,
               targetName='Organizador de Animes.exe', icon='geas.ico')
]

setup(name='Organizador',
      version='2.2',
      description='Organizador de Animes',
      options=options,
      executables=executables
      )
