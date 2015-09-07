from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [ctypes], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('main_gui.py', base=base, targetName = 'Phase.exe')
]

setup(name='Phase',
      version = '0.1',
      description = 'GUI for controlling phase masks for a LCoS SLM',
      options = dict(build_exe = buildOptions),
      executables = executables)
