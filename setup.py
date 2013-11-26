from distutils.core import setup
import py2exe
import glob
import os

from py2exe.build_exe import py2exe as build_exe

osgeopath = r'C:\OSGeo4W'
qtimageforms = os.path.join(osgeopath,r'apps\qt4\plugins\imageformats\*')

datafiles = [(".", [r'src\settings.config']),
            (r'libs\qmap', [r'src\qmap\info.html',
                            r'src\qmap\error.html']),
            (r'libs\qmap\bootstrap', glob.glob(r'src\qmap\bootstrap\*')),
            (r'projects', [r'projects\__init__.py']),
            # We have to copy the imageformat drivers to the root
            # folder.
            (r'imageformats', glob.glob(qtimageforms))]

roam_target = dict(
                script='src\qmap\__main__.py',
                dest_base='Roam',
                icon_resources=[(1, "src\icon.ico")]
            )

tests_target = dict(
                script='tests\__main__.py',
                dest_base='Roam_tests',
                icon_resources=[(1, "src\icon.ico")]
            )

setup(
    name='qmap',
    version='2.0',
    packages=['qmap', 'qmap.yaml', 'qmap.syncing', 'qmap.maptools', 'qmap.editorwidgets', 'qmap.editorwidgets.core',
              'qmap.editorwidgets.uifiles', '_install', 'tests'],
    package_dir={'': 'src', 'tests' : 'tests'},
    url='',
    license='GPL',
    author='nathan.woodrow',
    author_email='nathan.woodrow@mapsolutions.com.au',
    description='',
    windows=[roam_target],
    console=['src\_install\postinstall.py', tests_target],
    data_files=datafiles,
    zipfile='libs\\',
    options = {'py2exe': {
        'dll_excludes': [ 'msvcr80.dll', 'msvcp80.dll',
                        'msvcr80d.dll', 'msvcp80d.dll',
                        'powrprof.dll', 'mswsock.dll' ],
        'includes': ['PyQt4.QtNetwork', 'sip', 'PyQt4.QtSql'],
        'skip_archive': True,
      }},
)
