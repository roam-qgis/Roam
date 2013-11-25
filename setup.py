from distutils.core import setup
import py2exe
import glob

from py2exe.build_exe import py2exe as build_exe

datafiles = [(".", [r'src\settings.config']),
            (r'libs\qmap', [r'src\qmap\info.html',
                            r'src\qmap\error.html']),
            (r'libs\qmap\bootstrap', glob.glob(r'src\qmap\bootstrap\*')),
            (r'projects', [r'projects\__init__.py'])]

roam_target = dict(
                script='src\qmap\__main__.py',
                dest_base='Roam',
                icon_resources=[(1, "src\icon.ico")]
            )

setup(
    name='qmap',
    version='2.0',
    packages=['qmap', 'qmap.yaml', 'qmap.syncing', 'qmap.maptools', 'qmap.editorwidgets', 'qmap.editorwidgets.core',
              'qmap.editorwidgets.uifiles', '_install'],
    package_dir={'': 'src'},
    url='',
    license='GPL',
    author='nathan.woodrow',
    author_email='nathan.woodrow@mapsolutions.com.au',
    description='',
    windows=[roam_target],
    console=['src\_install\postinstall.py'],
    data_files=datafiles,
    zipfile='libs\\',
    options = {'py2exe': {
        'dll_excludes': [ 'msvcr80.dll', 'msvcp80.dll',
                        'msvcr80d.dll', 'msvcp80d.dll',
                        'powrprof.dll', 'mswsock.dll' ],
        'includes': ['PyQt4.QtNetwork', 'sip'],
        'skip_archive': True,
      }},
)
