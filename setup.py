import sys

from cx_Freeze import Executable, setup

from organizador.version import version

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'includes': ['atexit'],
                 'packages': ['queue', 'organizador'],
                 'zip_include_packages': ['pytz', 'PyQt5'],
                 'include_msvcr': True,
                 'optimize': 2}


base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('new_main_ui.py', base=base,
               target_name='Organizador de Series.exe', icon='icon.ico')
]

setup(name='Organizador',
      version=version,
      description='Organizador de Series',
      options={'build_exe': build_options},
      executables=executables)
