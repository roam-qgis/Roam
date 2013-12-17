from distutils.core import setup
from distutils.command.build import build
from fabricate import run

try:
    import py2exe
except ImportError:
    print "Can't import py2exe. Do you have it installed."

import glob
import os

# You are not meant to do this but we don't install using
# setup.py so no big deal.
import roam

osgeopath = r'C:\OSGeo4W'
osgeobin = os.path.join(osgeopath, 'bin')
qtimageforms = os.path.join(osgeopath,r'apps\qt4\plugins\imageformats\*')
qgisresources = os.path.join(osgeopath, "apps", "qgis", "resources")
svgs = os.path.join(osgeopath, "apps", "qgis", "svg")
qgispluginpath = os.path.join(osgeopath, r'apps\qgis\plugins\*provider.dll' )

def svgfiles():
    for path, dirs, files in os.walk(svgs):
        if not files: continue
        newpath = r'libs\qgis\svg\{}'.format(os.path.basename(path))
        collection = []
        for f in files:
            filename = os.path.join(path, f)
            collection.append(filename)
        yield (newpath, collection)

ecwfiles = [os.path.join(osgeobin, 'gdalplugins', 'gdal_ECW_JP2ECW.dll'),
            os.path.join(osgeobin, 'NCSEcw.dll')]

datafiles = [(".", [r'src\settings.config',
                    r'src\_install\_createshortcut.bat',
                    r'src\_install\shortcut.vbs']),
            (r'libs\roam', [r'src\roam\info.html',
                            r'src\roam\error.html']),
            (r'libs\roam\bootstrap', glob.glob(r'src\roam\bootstrap\*')),
            (r'projects', [r'src\projects\__init__.py']),
            # We have to copy the imageformat drivers to the root folder.
            (r'imageformats', glob.glob(qtimageforms)),
            (r'libs\qgis\plugins', glob.glob(qgispluginpath)),
            (r'libs\qgis\resources', [os.path.join(qgisresources, 'qgis.db'),
                                 os.path.join(qgisresources, 'srs.db')]),
            (r'libs', ecwfiles)]

for path, collection in svgfiles():
    datafiles.append((path, collection))

roam_target = dict(
                script=r'src\roam\__main__.py',
                dest_base='Roam',
                icon_resources=[(1, "src\icon.ico")]
            )

tests_target = dict(
                script=r'tests\__main__.py',
                dest_base='Roam_tests',
                icon_resources=[(1, "src\icon.ico")]
            )

projectupdater_target = dict(
                script=r'src\_install\postinstall.py',
                dest_base='Roam Project Updater',
                icon_resources=[(1, "src\icon.ico")]
            )


curpath = os.path.dirname(os.path.realpath(__file__))
appsrcopyFilesath = os.path.join(curpath, "src", 'roam')

def buildqtfiles():
    for root, dirs, files in os.walk(appsrcopyFilesath):
        for file in files:
            filepath = os.path.join(root, file)
            file, ext = os.path.splitext(filepath)
            if ext == '.ui':
                newfile = file + ".py"
                run('pyuic4.bat', '-o', newfile, filepath, shell=True)
            elif ext == '.qrc':
                newfile = file + "_rc.py"
                run('pyrcc4', '-o', newfile, filepath)


class qtbuild(build):
    def run(self):
        buildqtfiles()
        build.run(self)


setup(
    name='roam',
    version=roam.__version__,
    packages=['roam', 'roam.yaml', 'roam.syncing', 'roam.maptools', 'roam.editorwidgets', 'roam.editorwidgets.core',
              'roam.editorwidgets.uifiles', '_install', 'tests'],
    package_dir={'': 'src', 'tests' : 'tests'},
    url='',
    license='GPL',
    author='Digital Mapping Solutions',
    author_email='nathan.woodrow@mapsolutions.com.au',
    description='',
    windows=[roam_target],
    console=[tests_target, projectupdater_target],
    data_files=datafiles,
    zipfile='libs\\',
    cmdclass= {'build': qtbuild},
    options={'py2exe': {
        'dll_excludes': [ 'msvcr80.dll', 'msvcp80.dll',
                        'msvcr80d.dll', 'msvcp80d.dll',
                        'powrprof.dll', 'mswsock.dll',
                        'w9xpopen.exe', 'MSVCP90.dll'],
        'excludes': ['PyQt4.uic.port_v3'],
        'includes': ['PyQt4.QtNetwork', 'sip', 'PyQt4.QtSql'],
        'skip_archive': True,
      }},
)
