import os
import sys
sys.base_prefix = sys.prefix

from setuptools import find_packages
from distutils.core import setup
from distutils.core import setup
from distutils.command.build import build
from scripts.fabricate import run
from cx_Freeze import setup, Executable

# You are not meant to do this but we don't install using
# setup_py2exe.py so no big deal.
curpath = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(curpath, 'src'))
import roam


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"excludes": ["tcl"], "compressed": True}


setup(
    name='IntraMaps Roam',
    version="2.4.1.1",
    packages=find_packages('./src'),
    package_dir={'': 'src', 'tests': 'tests'},
    url='https://github.com/DMS-Aus/Roam',
    license='GPL',
    author='Nathan Woodrow',
    author_email='',
    description='',
    options = {"build_exe": build_exe_options},
    executables = [Executable(r"src\roam\__main__.py", base=base)]
)
